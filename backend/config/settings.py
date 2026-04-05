from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-replace-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "apps.users",
    "apps.authentication",
    "apps.access_control",
    "apps.business",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.authentication.middleware.JWTAuthMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="auth_db"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "users.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

JWT_ACCESS_TTL_MINUTES = config("JWT_ACCESS_TTL_MINUTES", default=15, cast=int)
JWT_REFRESH_TTL_DAYS = config("JWT_REFRESH_TTL_DAYS", default=30, cast=int)

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_TZ = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]
