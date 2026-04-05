from rest_framework import serializers
from .models import Role, Permission, RolePermission, UserRole


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "resource", "action"]

    def validate(self, data):
        qs = Permission.objects.filter(
            resource=data["resource"], action=data["action"]
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"Право {data['resource']}:{data['action']} уже существует."
            )
        return data


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "name", "description", "permissions"]
        read_only_fields = ["id", "permissions"]

    def get_permissions(self, obj):
        perms = Permission.objects.filter(role_permissions__role=obj)
        return PermissionSerializer(perms, many=True).data


class RoleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["name", "description"]

    def validate_name(self, value):
        value = value.strip()
        qs = Role.objects.filter(name=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"Роль '{value}' уже существует.")
        return value


class RolePermissionAddSerializer(serializers.Serializer):
    permission_id = serializers.UUIDField()

    def validate_permission_id(self, value):
        if not Permission.objects.filter(id=value).exists():
            raise serializers.ValidationError("Право с таким ID не найдено.")
        return value


class UserRoleAddSerializer(serializers.Serializer):
    role_id = serializers.UUIDField()

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Роль с таким ID не найдена.")
        return value


class UserRoleSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "role"]
