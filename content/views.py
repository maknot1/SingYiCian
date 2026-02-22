from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from content.emails import verify_email_token, send_confirm_email
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils.snippet import make_snippet
import uuid
import logging

logger = logging.getLogger(__name__)

from django import template
from .models import Section, Post, PostRevision, Activity, PostImage, UserProfile
from .forms import PostEditorForm, SectionForm, ProfileForm
from .permissions import publisher_required
from .utils.html import clean_html
from .utils.slug import generate_post_slug, generate_section_slug
from django.core.paginator import Paginator
from django.db.models import Max, OuterRef, Exists, Count, Q, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce


register = template.Library()

def get_sidebar_context(section=None, catalog=None):

    if section:
        catalog = section.catalog

    qs = Section.objects.filter(parent__isnull=True)

    if catalog:
        qs = qs.filter(catalog=catalog)

    root_sections = (
        qs.prefetch_related("children__children")
        .order_by("order", "title")
    )

    ancestor_ids = set()

    if section:
        ancestor_ids = {s.id for s in section.get_ancestors()}
        ancestor_ids.add(section.id)

    return {
        "root_sections": root_sections,
        "active_section": section,
        "ancestor_ids": ancestor_ids,
    }

@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


def is_publisher(user) -> bool:
    return user.is_authenticated and user.groups.filter(name="Publishers").exists()


def root_redirect(request):
    return redirect("/main/")


def home(request):
    sections = Section.objects.all()

    latest_posts = []
    if request.user.is_authenticated:
        latest_posts = (
            Post.objects
            .filter(status=Post.Status.PUBLISHED)
            .select_related("section")
            .order_by("-published_at")[:10]
        )

    return render(request, "content/public/home_public.html", {
        "sections": sections,
        "latest_posts": latest_posts,
        "sidebar_mode": "home",
    })


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":

        # повторная отправка письма
        if "resend_email" in request.POST:
            if profile.email and not profile.email_confirmed:
                send_confirm_email(request, profile)
                messages.success(
                    request,
                    "Письмо отправлено, проверьте почту"
                )
            return redirect("profile")

        # сохранение формы
        form = ProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save(request=request)
            messages.success(
                request,
                "Настройки профиля сохранены"
            )
            return redirect("profile")

    else:
        form = ProfileForm(instance=profile)

    return render(request, "content/internal/profile.html", {
        "profile": profile,
        "form": form,
    })

@login_required
def confirm_email(request, token):
    user_id, email = verify_email_token(token)

    if not user_id or not email:
        return render(request, "content/internal/email_confirm_invalid.html")

    try:
        profile = UserProfile.objects.get(user__id=user_id)
    except UserProfile.DoesNotExist:
        return render(request, "content/internal/email_confirm_invalid.html")

    if profile.email != email:
        return render(request, "content/internal/email_confirm_invalid.html")

    profile.email_confirmed = True
    profile.save(update_fields=["email_confirmed"])

    return render(request, "content/internal/email_confirm_success.html")

@login_required
def main(request):
    posts = (
        Post.objects
        .filter(status=Post.Status.PUBLISHED)
        .select_related("section", "author")
        .order_by(
            Coalesce("updated_at", "published_at").desc()
        )
    )

    paginator = Paginator(posts, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "content/internal/main.html", {
        "page_obj": page_obj,
    })


@login_required
def catalog_sinyi(request):
    q = request.GET.get("q", "").strip()

    sections = (
        Section.objects
        .filter(catalog="sinyi", parent__isnull=True)
        .prefetch_related("children__children")
        .order_by("order", "title")
    )

    search_qs = (
        Post.objects
        .filter(
            status=Post.Status.PUBLISHED,
            section__catalog="sinyi",
        )
        .select_related("section", "author", "current_revision")
    )

    featured_qs = search_qs.filter(is_featured=True)

    if q:
        result_qs = search_qs.filter(
            Q(title__icontains=q) |
            Q(summary__icontains=q) |
            Q(current_revision__content__icontains=q)
        ).order_by(
            "-is_featured",
            "order",
            "-published_at",
            "-created_at"
        )
    else:
        result_qs = featured_qs.order_by(
            "order",
            "-published_at",
            "-created_at"
        )

    paginator = Paginator(result_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    sidebar = get_sidebar_context(catalog="sinyi")

    return render(
        request,
        "content/internal/catalog_sinyi.html",
        {
            "catalog_title": "Синь И Цюань",
            "page_obj": page_obj,
            "active_catalog": "sinyi",
            "sidebar_mode": "catalog",
            "query": q,
            **sidebar,
        }
    )

@login_required
def catalog_taiji(request):
    q = request.GET.get("q", "").strip()

    search_qs = (
        Post.objects
        .filter(
            status=Post.Status.PUBLISHED,
            section__catalog="taiji",
        )
        .select_related("section", "author", "current_revision")
    )

    featured_qs = search_qs.filter(is_featured=True)

    if q:
        result_qs = search_qs.filter(
            Q(title__icontains=q) |
            Q(summary__icontains=q) |
            Q(current_revision__content__icontains=q)
        ).order_by(
            "-is_featured",
            "order",
            "-published_at",
            "-created_at"
        )
    else:
        result_qs = featured_qs.order_by(
            "order",
            "-published_at",
            "-created_at"
        )

    paginator = Paginator(result_qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    sidebar = get_sidebar_context(catalog="taiji")

    return render(
        request,
        "content/internal/catalog_taiji.html",
        {
            "catalog_title": "Тайцзи",
            "page_obj": page_obj,
            "active_catalog": "taiji",
            "sidebar_mode": "catalog",
            "query": q,
            **sidebar,
        }
    )

@login_required
def section_tree(request):
    sections = (
        Section.objects
        .filter(parent__isnull=True)
        .prefetch_related("children__children")
        .order_by("catalog", "order", "title")
    )

    return render(request, "content/internal/section_tree.html", {
        "sections": sections,
    })

@login_required
def section_search_api(request):
    logger.warning("SEARCH API HIT")
    logger.warning("GET PARAMS: %s", dict(request.GET))
    q = request.GET.get("q", "").strip()
    catalog = request.GET.get("catalog", "").strip()

    qs = Section.objects.all()

    if catalog:
        qs = qs.filter(catalog=catalog)

    if q:
        qs = qs.filter(title__icontains=q)

    print("QUERY:", q)
    print("CATALOG:", catalog)
    print("FOUND:", qs.count())

    data = [
        {
            "id": s.id,
            "slug": s.slug,
            "title": s.title,
            "depth": s.get_depth(),
        }
        for s in qs[:20]
    ]
    return JsonResponse(data, safe=False)

@login_required
def section_tree_page_api(request):
    page = int(request.GET.get("page", 1))
    per_page = 1
    catalog = request.GET.get("catalog")

    roots = Section.objects.filter(parent__isnull=True)

    if catalog:
        roots = roots.filter(catalog=catalog)

    roots = roots.order_by("order", "title")

    paginator = Paginator(roots, per_page)
    root_page = paginator.get_page(page)

    def serialize(node, depth=0):
        children_qs = node.children.all()

        if catalog:
            children_qs = children_qs.filter(catalog=catalog)

        return {
            "id": node.id,
            "title": node.title,
            "depth": depth,
            "children": [
                serialize(c, depth + 1)
                for c in children_qs
            ]
        }

    return JsonResponse({
        "pages": paginator.num_pages,
        "current": root_page.number,
        "data": [serialize(r, 0) for r in root_page.object_list]
    })


@login_required
def section_detail(request, slug):

    section = get_object_or_404(Section, slug=slug)
    query = request.GET.get("q", "").strip()

    ancestors = section.get_ancestors()
    ancestor_ids = {s.id for s in ancestors}
    ancestor_ids.add(section.id)

    children_qs = section.children.order_by("order", "title")

    children_page = None
    page_obj = None

    if children_qs.exists():
        paginator = Paginator(children_qs, 10)
        children_page = paginator.get_page(request.GET.get("cpage"))

    else:
        posts = (
            Post.objects
            .filter(
                section=section,
                status__in=[
                    Post.Status.PUBLISHED,
                    Post.Status.ARCHIVED
                ] if is_publisher(request.user)
                else [Post.Status.PUBLISHED]
            )
            .select_related("current_revision", "author")
        )

        if query:
            posts = posts.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query) |
                Q(current_revision__content__icontains=query)
            )

        posts = posts.order_by(
            "-is_featured",
            "order",
            "-published_at",
            "-created_at"
        )

        paginator = Paginator(posts, 10)
        page_obj = paginator.get_page(request.GET.get("page"))

    sidebar = get_sidebar_context(section)
    

    return render(
        request,
        "content/internal/section_detail.html",
        {
            "section": section,
            "ancestors": ancestors,
            "children_page": children_page,
            "page_obj": page_obj,
            "query": query,
            "sidebar_mode": "section",
            "can_edit": is_publisher(request.user),
            **sidebar,
        }
    )
@login_required
def post_detail(request, slug):
    qs = Post.objects.select_related("section", "author", "current_revision")

    if is_publisher(request.user):
        post = get_object_or_404(qs, slug=slug)
    else:
        post = get_object_or_404(qs, slug=slug, status=Post.Status.PUBLISHED)

    section = post.section if post.section and post.section.slug else None

    if section:
        section_posts_qs = section.posts.all()

        if not is_publisher(request.user):
            section_posts_qs = section_posts_qs.filter(
                status=Post.Status.PUBLISHED
            )

        section_posts_qs = section_posts_qs.order_by(
            "order",
            "-published_at"
        )
    else:
        section_posts_qs = Post.objects.none()

    sidebar = get_sidebar_context(post.section)

    return render(request, "content/internal/post_detail.html", {
        "post": post,
        "revision": post.current_revision,
        "section_posts": section_posts_qs,
        "active_section_slug": section.slug if section else None,
        "active_post_slug": post.slug,
        "sidebar_mode": "post",
        "can_edit": is_publisher(request.user),
        **sidebar,
    })

@login_required
def search(request):
    q = request.GET.get("q", "").strip()
    catalog = request.GET.get("catalog")

    results = Post.objects.none()

    if q:
        query = Q()

        for word in q.split():
            query |= (
                Q(title__icontains=word) |
                Q(summary__icontains=word) |
                Q(current_revision__content__icontains=word)
            )

        results = (
            Post.objects
            .filter(status=Post.Status.PUBLISHED)
            .filter(query)
        )

        if catalog:
            results = results.filter(section__catalog=catalog)

        results = results.distinct()

    return render(request, "content/internal/search.html", {
        "query": q,
        "results": results,
        "catalog": catalog,
        "sidebar_mode": "search",
    })


@login_required
def search_api(request):
    q = request.GET.get("q", "").strip()
    catalog = request.GET.get("catalog")
    section = request.GET.get("section")

    qs = (
        Post.objects
        .filter(status=Post.Status.PUBLISHED)
        .select_related("section", "current_revision")
    )

    if section:
        qs = qs.filter(section__slug=section)
    elif catalog:
        qs = qs.filter(section__catalog=catalog)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(current_revision__content__icontains=q)
        )

    qs = qs.distinct()[:5]

    data = []
    for post in qs:
        content = post.current_revision.content if post.current_revision else ""
        snippet = make_snippet(content, q)

        data.append({
            "title": post.title,
            "slug": post.slug,
            "section": post.section.title,
            "snippet": snippet,
        })

    return JsonResponse(data, safe=False)


@login_required
@publisher_required
def dashboard(request):
    posts = (
        Post.objects
        .exclude(status=Post.Status.ARCHIVED)
        .select_related('section')
        .order_by('-updated_at')
    )

    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'content/internal/dashboard.html', {
        'page_obj': page_obj,
    })


def _log_activity(*, post: Post, action: str, user):
    if not post.pk:
        return

    Activity.objects.create(
        post=post,
        title=post.title,
        section=post.section.title,
        action=action,
        user=user,
    )

@login_required
@publisher_required
@require_POST
def upload_editor_image(request):
    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"error": "no image"}, status=400)

    img = PostImage.objects.create(
        post=None,
        image=image,
        title=image.name,
    )

    return JsonResponse({"url": img.image.url})

@login_required
@publisher_required
def create_post(request):
    if request.method == "POST":
        form = PostEditorForm(request.POST, request.FILES)

        if form.is_valid():
            content = clean_html(form.cleaned_data["content"]).strip()
            if not content:
                form.add_error(None, "Текст статьи пуст")
            else:
                section = form.cleaned_data["section"]
                status = form.cleaned_data["status"]

                is_featured = (
                    "is_featured" in request.POST
                    and status == Post.Status.PUBLISHED
                )

                post = Post.objects.create(
                    section=section,
                    title=form.cleaned_data["title"],
                    status=status,
                    author=request.user,
                    is_featured=is_featured,
                    published_at=(
                        timezone.now()
                        if status == Post.Status.PUBLISHED
                        else None
                    ),
                )

                revision = PostRevision.objects.create(
                    post=post,
                    content=content,
                    note=form.cleaned_data.get("note", ""),
                    created_by=request.user,
                    is_published_snapshot=(status == Post.Status.PUBLISHED),
                )

                post.current_revision = revision
                post.save(update_fields=["current_revision"])

                _log_activity(post=post, action="create", user=request.user)

                if status == Post.Status.PUBLISHED:
                    _log_activity(post=post, action="publish", user=request.user)

                return redirect("post_detail", slug=post.slug)

    else:
        form = PostEditorForm(initial={
            "status": Post.Status.PUBLISHED
        })

    return render(request, "content/internal/post_editor.html", {
        "form": form,
        "mode": "create",
    })


@login_required
@publisher_required
def edit_post(request, post_slug):
    post = get_object_or_404(
        Post.objects.select_related("section", "current_revision"),
        slug=post_slug
    )

    old_status = post.status

    if request.method == "POST":
        form = PostEditorForm(request.POST, request.FILES)

        if form.is_valid():
            content = clean_html(form.cleaned_data["content"]).strip()
            if not content:
                form.add_error(None, "Текст статьи пуст")
            else:
                post.section = form.cleaned_data["section"]
                post.title = form.cleaned_data["title"]
                post.status = form.cleaned_data["status"]

                # 🔒 ЖЁСТКАЯ ЛОГИКА ЗАКРЕПА
                if post.status == Post.Status.PUBLISHED:
                    post.is_featured = "is_featured" in request.POST
                else:
                    post.is_featured = False

                # 📅 дата публикации ставится только при первом publish
                if post.status == Post.Status.PUBLISHED and not post.published_at:
                    post.published_at = timezone.now()

                revision = PostRevision.objects.create(
                    post=post,
                    content=content,
                    note=form.cleaned_data.get("note", ""),
                    created_by=request.user,
                    is_published_snapshot=(post.status == Post.Status.PUBLISHED),
                )

                post.current_revision = revision
                post.save()

                _log_activity(post=post, action="update", user=request.user)

                if old_status != post.status:
                    if post.status == Post.Status.PUBLISHED:
                        _log_activity(post=post, action="publish", user=request.user)
                    elif post.status == Post.Status.ARCHIVED:
                        _log_activity(post=post, action="archive", user=request.user)

                return redirect("post_detail", slug=post.slug)

    else:
        form = PostEditorForm(initial={
            "section": post.section,
            "title": post.title,
            "content": post.current_revision.content if post.current_revision else "",
            "status": post.status,
            "note": post.current_revision.note if post.current_revision else "",
            "is_featured": post.is_featured,
        })

    return render(request, "content/internal/post_editor.html", {
        "form": form,
        "mode": "edit",
        "post": post,
    })



@login_required
@publisher_required
@require_POST
def publish_post(request, slug):
    """
    Совместимость со старым интерфейсом (кнопка в таблице dashboard).
    Можно оставить, но теперь основной путь - через edit_post.
    """
    post = get_object_or_404(Post, slug=slug)
    post.status = Post.Status.PUBLISHED
    if not post.published_at:
        post.published_at = timezone.now()
    post.save()

    _log_activity(post=post, action="publish", user=request.user)

    return redirect("dashboard")


@login_required
@publisher_required
@require_POST
def archive_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    post.status = Post.Status.ARCHIVED
    post.is_featured = False
    post.save(update_fields=["status", "is_featured"])

    _log_activity(post=post, action="archive", user=request.user)

    return redirect("dashboard")

@login_required
@publisher_required
def archived_posts(request):
    posts = (
        Post.objects
        .filter(status=Post.Status.ARCHIVED)
        .select_related("section", "author")
        .order_by("-updated_at")
    )

    paginator = Paginator(posts, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "content/internal/dashboard.html", {
        "page_obj": page_obj,
        "mode": "archive",
    })

@login_required
@publisher_required
@require_POST
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug)

    _log_activity(
        post=post,
        action="delete",
        user=request.user,
    )
    post.delete()

    return redirect("dashboard")



@login_required
@publisher_required
def create_section(request):
    section = None

    if request.method == "POST":
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)


            section.slug = generate_section_slug(section.title)

            section.save()
            return redirect("section_list")
    else:
        form = SectionForm()

    return render(request, "content/internal/section_editor.html", {
        "form": form,
        "section": section,
        "mode": "create",
    })




from django.db.models import ProtectedError
from django.contrib import messages

@login_required
@publisher_required
@require_POST
def delete_section(request, slug):
    section = get_object_or_404(Section, slug=slug)

    # 🚫 есть статьи
    if section.posts.exists():
        messages.error(
            request,
            "Нельзя удалить раздел, пока в нём есть статьи (включая архив)"
        )
        return redirect("section_edit", slug=section.slug)

    # 🚫 есть подразделы
    if section.children.exists():
        messages.error(
            request,
            "Нельзя удалить раздел, пока в нём есть подразделы"
        )
        return redirect("section_edit", slug=section.slug)

    try:
        section.delete()
        messages.success(request, "Раздел удалён")
    except ProtectedError:
        messages.error(
            request,
            "Раздел нельзя удалить, так как он используется"
        )

    return redirect("section_list")



@login_required
@publisher_required
def section_list(request):
    section_type = request.GET.get("type", "group")  # например дефолт на group

    base_qs = Section.objects.annotate(posts_count=Count("posts"))

    # счётчики
    counts = {
        "container": base_qs.filter(parent__isnull=True).count(),
        "group": base_qs.filter(parent__isnull=False, parent__parent__isnull=True).count(),
        "content": base_qs.filter(parent__parent__isnull=False).count(),
    }

    # фильтр для текущей вкладки
    if section_type == "container":
        sections_qs = base_qs.filter(parent__isnull=True)
    elif section_type == "content":
        sections_qs = base_qs.filter(parent__parent__isnull=False)
    else:  # group
        sections_qs = base_qs.filter(parent__isnull=False, parent__parent__isnull=True)

    sections_qs = sections_qs.order_by("title")

    paginator = Paginator(sections_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "content/internal/section_list.html", {
        "page_obj": page_obj,
        "section_type": section_type,
        "counts": counts,
    })


@login_required
@publisher_required
def edit_section(request, slug):
    section = get_object_or_404(Section, slug=slug)

    if request.method == "POST":
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            section = form.save(commit=False)

            # если slug пустой - пересоздаём
            if not section.slug:
                section.slug = generate_section_slug(section.title)

            section.save()
            return redirect("section_list")
    else:
        form = SectionForm(instance=section)

    return render(request, "content/internal/section_editor.html", {
        "form": form,
        "section": section,
        "mode": "edit",
    })

