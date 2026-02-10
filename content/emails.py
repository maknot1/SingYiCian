from django.core.mail import send_mail
from django.urls import reverse
from django.core.signing import TimestampSigner
from django.conf import settings
signer = TimestampSigner()

# ===== EMAIL CONFIRM =====

def make_email_token(user_id, email):
    return signer.sign(f"{user_id}:{email}")

def verify_email_token(token, max_age=60 * 60 * 24):
    try:
        value = signer.unsign(token, max_age=max_age)
        user_id, email = value.split(":", 1)
        return int(user_id), email
    except Exception:
        return None, None



def send_confirm_email(request, profile):
    token = make_email_token(
        profile.user.id,
        profile.email
    )

    confirm_url = request.build_absolute_uri(
        reverse("confirm_email", args=[token])
    )

    send_mail(
        subject="Подтверждение email",
        message=(
            "Вы указали этот email для получения уведомлений.\n\n"
            f"Подтвердите адрес по ссылке:\n{confirm_url}"
        ),
        from_email=None,
        recipient_list=[profile.email],
        fail_silently=False,
    )

# ===== POSTS =====

def send_new_post_email(email, post):
    url = settings.SITE_URL + post.get_absolute_url()

    send_mail(
        subject=f"Новая публикация: {post.title}",
        message=(
            "Опубликована новая статья:\n\n"
            f"{post.title}\n\n"
            f"Читать статью:\n{url}"
        ),
        from_email=None,
        recipient_list=[email],
        fail_silently=True,
    )

def send_post_update_email(email, post):
    url = settings.SITE_URL + post.get_absolute_url()

    send_mail(
        subject=f"Обновление статьи: {post.title}",
        message=(
            "Статья была обновлена:\n\n"
            f"{post.title}\n\n"
            f"Открыть статью:\n{url}"
        ),
        from_email=None,
        recipient_list=[email],
        fail_silently=True,
    )

