from django.db import models
from django.conf import settings
from django.utils import timezone

class Section(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='sections/covers/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Порядок отображения (меньше - выше")

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

class Tag(models.Model):
    title = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self) -> str:
        return self.title

from django.conf import settings
from django.db import models
from django.utils import timezone


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликовано'
        ARCHIVED = 'archived', 'Архив'

    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name='posts'
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    summary = models.TextField(
        blank=True,
        help_text="Короткое описание для списков"
    )
    cover_image = models.ImageField(
        upload_to='posts/covers/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Закрепить в разделе или на главной"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Порядок внутри раздела"
    )

    published_at = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts_authored'
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts'
    )

    # 🔑 КЛЮЧЕВОЕ ПОЛЕ
    current_revision = models.ForeignKey(
        'PostRevision',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text="Ревизия, отображаемая на сайте"
    )

    class Meta:
        ordering = ['order', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['section', 'status']),
        ]

    def __str__(self) -> str:
        return self.title

    def publish(self) -> None:
        """
        Публикует статью (меняет статус и дату).
        Контент определяется current_revision.
        """
        self.status = self.Status.PUBLISHED
        if not self.published_at:
            self.published_at = timezone.now()

    @property
    def is_visible(self) -> bool:
        return self.status == self.Status.PUBLISHED


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
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

