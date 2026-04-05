from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

from .services import validate_access_token

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    DRF-аутентификация через Bearer JWT-токен.
    Читает заголовок Authorization: Bearer <token>,
    валидирует токен и возвращает пользователя.
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        raw_token = auth_header.split(" ", 1)[1].strip()
        if not raw_token:
            return None

        try:
            payload = validate_access_token(raw_token)
        except ValueError as exc:
            raise AuthenticationFailed(str(exc))

        try:
            user = User.objects.get(id=payload["sub"], is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed("Пользователь не найден или деактивирован.")

        return (user, raw_token)

    def authenticate_header(self, request):
        return "Bearer"
