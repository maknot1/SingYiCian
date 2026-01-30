from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Post, PostRevision


@receiver(post_save, sender=Post)
def ensure_initial_revision(sender, instance: Post, created: bool, **kwargs):
    if not created:
        return

    revision = PostRevision.objects.create(
        post=instance,
        content="",
        created_by=instance.author,
        note="Initial revision",
        is_published_snapshot=(instance.status == Post.Status.PUBLISHED),
    )

    instance.current_revision = revision
    instance.save(update_fields=['current_revision'])

@receiver(post_save, sender=Post)
def ensure_published_at(sender, instance: Post, created: bool, **kwargs):
    """
    Если статус опубликован, а published_at не задан - проставляем.
    """
    if instance.status == Post.Status.PUBLISHED and not instance.published_at:
        Post.objects.filter(pk=instance.pk).update(published_at=timezone.now())
