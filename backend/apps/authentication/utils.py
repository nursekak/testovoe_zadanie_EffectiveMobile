from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_authenticated(method):
    """Декоратор: требует аутентификацию через JWT."""
    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        if not request.user or not getattr(request.user, "is_active", False):
            return Response(
                {"detail": "Аутентификация обязательна."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return method(self, request, *args, **kwargs)
    return wrapper
