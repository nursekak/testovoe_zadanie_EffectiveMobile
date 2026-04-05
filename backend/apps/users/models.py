import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password, first_name, last_name, middle_name=""):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, first_name="Admin", last_name="Admin"):
        user = self.create_user(email, password, first_name, last_name)
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users_user"
        verbose_name = "Пользователь"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def has_permission(self, resource: str, action: str) -> bool:
        from apps.access_control.models import UserRole
        role_ids = UserRole.objects.filter(user=self).values_list("role_id", flat=True)
        from apps.access_control.models import RolePermission
        return RolePermission.objects.filter(
            role_id__in=role_ids,
            permission__resource=resource,
            permission__action=action,
        ).exists()
