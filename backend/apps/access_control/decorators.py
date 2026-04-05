from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_permission(resource: str, action: str):
    def decorator(method):
        @wraps(method)
        def wrapper(self, request, *args, **kwargs):
            user = request.user
            if not user or not getattr(user, "is_active", False):
                return Response(
                    {"detail": "Аутентификация обязательна."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not user.has_permission(resource, action):
                return Response(
                    {"detail": f"Нет доступа: требуется {resource}:{action}."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return method(self, request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(method):
    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        user = request.user
        if not user or not getattr(user, "is_active", False):
            return Response(
                {"detail": "Аутентификация обязательна."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.has_permission("admin", "access"):
            return Response(
                {"detail": "Требуется роль администратора."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return method(self, request, *args, **kwargs)
    return wrapper
