import uuid
from django.db import models
from django.conf import settings


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "access_control_role"
        verbose_name = "Роль"

    def __str__(self):
        return self.name


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource = models.CharField(max_length=64)
    action = models.CharField(max_length=32)

    class Meta:
        db_table = "access_control_permission"
        verbose_name = "Право"
        unique_together = [("resource", "action")]

    def __str__(self):
        return f"{self.resource}:{self.action}"


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="role_permissions")

    class Meta:
        db_table = "access_control_rolepermission"
        unique_together = [("role", "permission")]

    def __str__(self):
        return f"{self.role.name} → {self.permission}"


class UserRole(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")

    class Meta:
        db_table = "access_control_userrole"
        unique_together = [("user", "role")]

    def __str__(self):
        return f"{self.user.email} → {self.role.name}"
