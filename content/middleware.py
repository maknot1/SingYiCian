from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # --- НЕАВТОРИЗОВАННЫЕ ---
        if not request.user.is_authenticated:

            # login всегда доступен
            if path == settings.LOGIN_URL:
                return self.get_response(request)

            # admin доступен
            if path.startswith('/admin/'):
                return self.get_response(request)

            # статика и медиа
            if path.startswith(settings.STATIC_URL):
                return self.get_response(request)

            if settings.MEDIA_URL and path.startswith(settings.MEDIA_URL):
                return self.get_response(request)

            # ВСЁ ОСТАЛЬНОЕ — ЗАКРЫТО
            return redirect(settings.LOGIN_URL)

        # --- АВТОРИЗОВАННЫЕ ---
        # корень / временно закрыт
        if path == '/':
            return redirect('/main/')

        return self.get_response(request)
