from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction

from .models import UserProfile, Post, PostRevision
from .emails import send_new_post_email, send_post_update_email  # <-- важно

User = get_user_model()

print("SIGNALS LOADED", __name__)

@receiver(post_save, sender=User, dispatch_uid="create_user_profile_once")
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=Post)
def notify_new_post(sender, instance, created, **kwargs):
    if not created:
        return

    post = instance  # 🔹 ЯВНО фиксируем

    cache.set(f"post_just_created:{post.pk}", True, timeout=30)

    def _send():
        profiles = UserProfile.objects.select_related("user")
        for profile in profiles:
            if (
                profile.email
                and profile.email_confirmed
                and profile.notify_new_posts
            ):
                send_new_post_email(profile.email, post)

    transaction.on_commit(_send)



@receiver(
    post_save,
    sender=PostRevision,
    dispatch_uid="notify_post_update_once"
)
def notify_post_update(sender, instance, created, **kwargs):
    if not created:
        return

    post = instance.post

    # если пост только что создан — это часть публикации, не обновление
    if cache.get(f"post_just_created:{post.pk}"):
        return

    # обновления шлём только для опубликованных статей
    if post.status != Post.Status.PUBLISHED:
        return

    def _send():
        profiles = UserProfile.objects.select_related("user")

        for profile in profiles:
            if (
                profile.email
                and profile.email_confirmed
                and profile.notify_updates
            ):
                send_post_update_email(profile.email, post)

    transaction.on_commit(_send)


@receiver(post_save, sender=Post, dispatch_uid="ensure_initial_revision_once")
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

    # ВАЖНО: update() не вызывает сигналы Post, в отличие от instance.save()
    Post.objects.filter(pk=instance.pk).update(current_revision=revision)


@receiver(post_save, sender=Post, dispatch_uid="ensure_published_at_once")
def ensure_published_at(sender, instance: Post, created: bool, **kwargs):
    """
    Если статус опубликован, а published_at не задан - проставляем.
    """
    if instance.status == Post.Status.PUBLISHED and not instance.published_at:
        Post.objects.filter(pk=instance.pk).update(published_at=timezone.now())
