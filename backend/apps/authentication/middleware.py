from django.contrib.auth import get_user_model
from django.utils.functional import SimpleLazyObject

from .services import validate_access_token

User = get_user_model()


def _get_user_from_request(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    raw_token = auth_header.split(" ", 1)[1].strip()
    if not raw_token:
        return None
    try:
        payload = validate_access_token(raw_token)
    except ValueError:
        return None
    try:
        user = User.objects.get(id=payload["sub"], is_active=True)
    except User.DoesNotExist:
        return None
    return user


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = SimpleLazyObject(lambda: _get_user_from_request(request))
        return self.get_response(request)
