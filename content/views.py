from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Section, Post, PostRevision
from .forms import PostCreateForm, PostRevisionForm
from .permissions import publisher_required
from .utils.html import clean_html



def home(request):
    """
    Публичная главная страница.
    Гость видит описание школы и направлений.
    Авторизованный пользователь дополнительно видит свежие публикации.
    """

    sections = Section.objects.all()

    latest_posts = []
    if request.user.is_authenticated:
        latest_posts = (
            Post.objects
            .filter(status=Post.Status.PUBLISHED)
            .select_related('section')
            .order_by('-published_at')[:10]
        )

    return render(request, 'content/home.html', {
        'sections': sections,
        'latest_posts': latest_posts,
        'sidebar_mode': 'home',
    })


@login_required
def section_detail(request, slug):
    section = get_object_or_404(Section, slug=slug)

    posts = (
        section.posts
        .filter(status=Post.Status.PUBLISHED)
        .order_by('order', '-published_at')
    )

    return render(request, 'content/section_detail.html', {
        'section': section,
        'posts': posts,
        'sidebar_mode': 'section',
        'active_section_slug': section.slug,
    })


@login_required
def post_detail(request, slug):
    post = get_object_or_404(
        Post,
        slug=slug,
        status=Post.Status.PUBLISHED
    )

    section_posts = (
        post.section.posts
        .filter(status=Post.Status.PUBLISHED)
        .order_by('order', '-published_at')
    )

    return render(request, 'content/post_detail.html', {
        'post': post,
        'revision': post.current_revision,
        'section_posts': section_posts,
        'active_section_slug': post.section.slug,
        'active_post_slug': post.slug,
        'sidebar_mode': 'post',
    })


@login_required
@publisher_required
def dashboard(request):
    posts = (
        Post.objects
        .select_related('section')
        .order_by('-updated_at')
    )

    return render(request, 'content/dashboard.html', {
        'posts': posts,
    })


@login_required
@publisher_required
def create_post(request):
    if request.method == 'POST':
        form = PostCreateForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            return redirect('create_revision', post_slug=post.slug)
    else:
        form = PostCreateForm()

    return render(request, 'content/post_form.html', {
        'form': form,
    })


@login_required
@publisher_required
def create_revision(request, post_slug):
    post = get_object_or_404(Post, slug=post_slug)

    if request.method == 'POST':
        form = PostRevisionForm(request.POST)
        if form.is_valid():
            revision = form.save(commit=False)
            revision.post = post
            revision.created_by = request.user
            revision.content = clean_html(revision.content)
            revision.save()
            return redirect('post_detail', slug=post.slug)
    else:
        initial = {}
        if post.current_revision:
            initial['content'] = post.current_revision.content
        form = PostRevisionForm(initial=initial)

    return render(request, 'content/revision_form.html', {
        'post': post,
        'form': form,
    })


@login_required
@publisher_required
def make_revision_current(request, revision_id):
    revision = get_object_or_404(PostRevision, id=revision_id)
    post = revision.post

    post.current_revision = revision
    post.save(update_fields=['current_revision'])

    return redirect('post_detail', slug=post.slug)


@login_required
@publisher_required
@require_POST
def publish_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.status = Post.Status.PUBLISHED

    if not post.published_at:
        post.published_at = timezone.now()

    post.save()
    return redirect('dashboard')


@login_required
@publisher_required
@require_POST
def archive_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    post.status = Post.Status.ARCHIVED
    post.save()

    return redirect('dashboard')
