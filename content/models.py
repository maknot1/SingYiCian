from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import User
from slugify import slugify
from django.core.exceptions import ValidationError
from django.urls import reverse
import uuid


User = get_user_model()



class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    # === ПОДТВЕРЖДЕНИЕ EMAIL ===
    email_confirmed = models.BooleanField(
        default=False
    )

    # === УВЕДОМЛЕНИЯ ===
    notify_new_posts = models.BooleanField(
        default=True,
        verbose_name="Уведомлять о новых публикациях"
    )

    notify_updates = models.BooleanField(
        default=True,
        verbose_name="Уведомлять об обновлениях статей"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Profile: {self.user.username}"


class Section(models.Model):
    CATALOG_CHOICES = [
        ("sinyi", "Синь И Цюань"),
        ("taiji", "Тайцзи"),
        ("classes", "Занятия"),
    ]

    title = models.CharField(max_length=200)

    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
    )

    description = models.TextField(blank=True)

    catalog = models.CharField(
        max_length=50,
        choices=CATALOG_CHOICES,
        default="sinyi",
        verbose_name="Каталог"
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
        db_index=True,
        verbose_name="Родительский раздел"
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def get_ancestors(self):
        ancestors = []
        node = self.parent

        while node:
            ancestors.insert(0, node)
            node = node.parent

        return ancestors

    def get_absolute_url(self):
        return reverse("section_detail", kwargs={"slug": self.slug})

    def get_depth(self):
        depth = 0
        node = self.parent
        while node:
            depth += 1
            node = node.parent
        return depth

    def clean(self):
        if self.parent:
            if self.parent.get_depth() >= 2:
                raise ValidationError(
                    "Допускается не более 3 уровней вложенности разделов"
                )

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.slug and self.title:
            base = slugify(self.title) or "section"
            slug = base
            counter = 1

            while Section.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)


class Post(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликовано'
        ARCHIVED = 'archived', 'Архив'

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name="Раздел"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="Заголовок"
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name="URL"
    )

    summary = models.TextField(
        blank=True,
        verbose_name="Краткое описание"
    )

    cover_image = models.ImageField(
        upload_to='posts/covers/',
        blank=True,
        null=True,
        verbose_name="Обложка"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Статус"
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Закреплённая"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок"
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата публикации"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts_authored',
        verbose_name="Автор"
    )

    current_revision = models.ForeignKey(
        'PostRevision',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Текущая версия"
    )


    class Meta:
        ordering = ['order', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['section', 'status']),
        ]
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base = slugify(self.title)

            if not base:
                base = "post"

            slug = base
            counter = 1

            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="bookmarked_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.post}"

class PostImage(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='images',
        null=True,
        blank=True
    )
    image = models.ImageField(upload_to='posts/images/')
    title = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return self.title or f"Image #{self.id} for {self.post_id}"


class PostRevision(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='revisions')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='post_revisions'
    )
    note = models.CharField(max_length=200, blank=True, help_text="Короткая заметка: что изменилось")
    is_published_snapshot = models.BooleanField(default=False, help_text="Снимок в момент публикации")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]

    def __str__(self) -> str:
        return f"Revision {self.id} - {self.post.title}"

class Activity(models.Model):
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('publish', 'Публикация'),
        ('archive', 'Архив'),
        ('delete', 'Удаление'),
    ]

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="activities"
    )

    title = models.CharField(max_length=255)
    section = models.CharField(max_length=100)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.action})"

