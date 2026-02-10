from django import forms
from .models import Post, Section, UserProfile
from django.core.exceptions import ValidationError
from django.db.models import Count
import uuid
from content.emails import send_confirm_email

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["email", "notify_new_posts", "notify_updates"]

    def save(self, request=None, commit=True):
        profile = super().save(commit=False)

        if "email" in self.changed_data:
            profile.email_confirmed = False

            if commit:
                profile.save()

            if profile.email and request:
                send_confirm_email(request, profile)
        else:
            if commit:
                profile.save()

        return profile

class SectionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        depth = obj.get_depth()
        prefix = "—" * depth
        return f"{prefix} {obj.title}" if prefix else obj.title


class PostEditorForm(forms.Form):
    STATUS_CHOICES = [
        (Post.Status.PUBLISHED, "Опубликовано"),
        (Post.Status.ARCHIVED, "Архив"),
    ]

    section = forms.ModelChoiceField(
        queryset=Section.objects
        .annotate(children_count=Count("children"))
        .filter(children_count=0),
        label="Раздел"
    )

    title = forms.CharField(
        max_length=255,
        label="Заголовок",
    )

    content = forms.CharField(
        required=True,
        widget=forms.Textarea,
        label="Текст статьи"
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect,
        label="Статус"
    )

    is_featured = forms.BooleanField(
        required=False,
        label="Закрепить статью"
    )

    note = forms.CharField(
        required=False,
        label="Заметка"
    )

    def clean_content(self):
        content = (self.cleaned_data.get("content") or "").strip()
        if not content or content in ("<p><br></p>", "<p></p>"):
            raise forms.ValidationError("Текст статьи не может быть пустым.")
        return content

class SectionForm(forms.ModelForm):

    parent = SectionChoiceField(
        queryset=Section.objects.none(),
        required=False,
        label="Родительский раздел"
    )

    class Meta:
        model = Section
        fields = ["title", "catalog", "parent"]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Название раздела"
            }),
            "catalog": forms.Select(attrs={
                "class": "form-control",
            }),
            "parent": forms.Select(attrs={
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["parent"].required = False

        # 1. Определяем каталог
        catalog = None

        if self.instance.pk:
            catalog = self.instance.catalog
        elif self.data.get("catalog"):
            catalog = self.data.get("catalog")
        else:
            # 🔥 ВАЖНО: GET / create → разрешаем ВСЕ каталоги
            qs = Section.objects.all()
            self._apply_parent_rules(qs)
            return

        # 2. Фильтр по каталогу
        qs = Section.objects.filter(catalog=catalog)

        # 3. Исключения при редактировании
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            qs = qs.exclude(pk__in=self._get_descendants(self.instance))

        self._apply_parent_rules(qs)

    def _apply_parent_rules(self, qs):
        allowed_ids = [
            s.pk for s in qs
            if s.get_depth() < 2
        ]

        self.fields["parent"].queryset = (
            qs.filter(pk__in=allowed_ids)
            .order_by("catalog", "order", "title")
        )

    def _get_descendants(self, section):
        """
        Возвращает список id всех потомков раздела (любой глубины)
        """
        ids = []

        def collect(node):
            for child in node.children.all():
                ids.append(child.pk)
                collect(child)

        collect(section)
        return ids