import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone

from django.conf import settings

from .models import RefreshToken


def _now():
    return datetime.now(tz=timezone.utc)


def generate_access_token(user) -> str:
    ttl = settings.JWT_ACCESS_TTL_MINUTES
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": _now(),
        "exp": _now() + timedelta(minutes=ttl),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def validate_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Токен истёк.")
    except jwt.InvalidTokenError:
        raise ValueError("Недействительный токен.")
    if payload.get("type") != "access":
        raise ValueError("Неверный тип токена.")
    return payload


def generate_refresh_token(user) -> str:
    raw_token = secrets.token_hex(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    ttl = settings.JWT_REFRESH_TTL_DAYS
    RefreshToken.objects.create(
        user=user,
        token_hash=token_hash,
        expires_at=_now() + timedelta(days=ttl),
    )
    return raw_token


def rotate_refresh_token(raw_token: str):
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        stored = RefreshToken.objects.select_related("user").get(
            token_hash=token_hash,
            revoked=False,
        )
    except RefreshToken.DoesNotExist:
        raise ValueError("Refresh-токен не найден или уже отозван.")

    if stored.expires_at < _now():
        stored.revoked = True
        stored.save(update_fields=["revoked"])
        raise ValueError("Refresh-токен истёк.")

    user = stored.user
    if not user.is_active:
        raise ValueError("Пользователь деактивирован.")

    stored.revoked = True
    stored.save(update_fields=["revoked"])

    new_access = generate_access_token(user)
    new_refresh = generate_refresh_token(user)
    return user, new_access, new_refresh


def revoke_refresh_token(raw_token: str) -> bool:
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    updated = RefreshToken.objects.filter(
        token_hash=token_hash, revoked=False
    ).update(revoked=True)
    return updated > 0
