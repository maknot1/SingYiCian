from functools import wraps
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST


def is_publisher(user) -> bool:
    return user.is_authenticated and user.groups.filter(name="Publishers").exists()


def publisher_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_publisher(request.user):
            return HttpResponseForbidden("Недостаточно прав")
        return view_func(request, *args, **kwargs)
    return _wrapped
