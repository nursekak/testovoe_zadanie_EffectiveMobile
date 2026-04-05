from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Role, Permission, RolePermission, UserRole
from .serializers import (
    RoleSerializer,
    RoleWriteSerializer,
    PermissionSerializer,
    RolePermissionAddSerializer,
    UserRoleAddSerializer,
    UserRoleSerializer,
)
from .decorators import require_admin

User = get_user_model()


class RoleListView(APIView):
    @require_admin
    def get(self, request):
        roles = Role.objects.all().order_by("name")
        return Response(RoleSerializer(roles, many=True).data)

    @require_admin
    def post(self, request):
        serializer = RoleWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        role = serializer.save()
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    def _get_role(self, pk):
        try:
            return Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return None

    @require_admin
    def get(self, request, pk):
        role = self._get_role(pk)
        if not role:
            return Response({"detail": "Роль не найдена."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RoleSerializer(role).data)

    @require_admin
    def patch(self, request, pk):
        role = self._get_role(pk)
        if not role:
            return Response({"detail": "Роль не найдена."}, status=status.HTTP_404_NOT_FOUND)
        serializer = RoleWriteSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(RoleSerializer(role).data)

    @require_admin
    def delete(self, request, pk):
        role = self._get_role(pk)
        if not role:
            return Response({"detail": "Роль не найдена."}, status=status.HTTP_404_NOT_FOUND)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermissionListView(APIView):
    @require_admin
    def get(self, request):
        perms = Permission.objects.all().order_by("resource", "action")
        return Response(PermissionSerializer(perms, many=True).data)

    @require_admin
    def post(self, request):
        serializer = PermissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        perm = serializer.save()
        return Response(PermissionSerializer(perm).data, status=status.HTTP_201_CREATED)


class PermissionDetailView(APIView):
    def _get_perm(self, pk):
        try:
            return Permission.objects.get(pk=pk)
        except Permission.DoesNotExist:
            return None

    @require_admin
    def get(self, request, pk):
        perm = self._get_perm(pk)
        if not perm:
            return Response({"detail": "Право не найдено."}, status=status.HTTP_404_NOT_FOUND)
        return Response(PermissionSerializer(perm).data)

    @require_admin
    def patch(self, request, pk):
        perm = self._get_perm(pk)
        if not perm:
            return Response({"detail": "Право не найдено."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PermissionSerializer(perm, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(PermissionSerializer(perm).data)

    @require_admin
    def delete(self, request, pk):
        perm = self._get_perm(pk)
        if not perm:
            return Response({"detail": "Право не найдено."}, status=status.HTTP_404_NOT_FOUND)
        perm.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionsView(APIView):
    def _get_role(self, pk):
        try:
            return Role.objects.get(pk=pk)
        except Role.DoesNotExist:
            return None

    @require_admin
    def get(self, request, pk):
        role = self._get_role(pk)
        if not role:
            return Response({"detail": "Роль не найдена."}, status=status.HTTP_404_NOT_FOUND)
        perms = Permission.objects.filter(role_permissions__role=role)
        return Response(PermissionSerializer(perms, many=True).data)

    @require_admin
    def post(self, request, pk):
        role = self._get_role(pk)
        if not role:
            return Response({"detail": "Роль не найдена."}, status=status.HTTP_404_NOT_FOUND)
        serializer = RolePermissionAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        perm = Permission.objects.get(id=serializer.validated_data["permission_id"])
        _, created = RolePermission.objects.get_or_create(role=role, permission=perm)
        if not created:
            return Response(
                {"detail": "Это право уже назначено роли."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(PermissionSerializer(perm).data, status=status.HTTP_201_CREATED)


class RolePermissionDeleteView(APIView):
    @require_admin
    def delete(self, request, pk, perm_id):
        deleted, _ = RolePermission.objects.filter(
            role_id=pk, permission_id=perm_id
        ).delete()
        if not deleted:
            return Response({"detail": "Связь не найдена."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRolesView(APIView):
    def _get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @require_admin
    def get(self, request, user_id):
        target = self._get_user(user_id)
        if not target:
            return Response({"detail": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)
        user_roles = UserRole.objects.filter(user=target).select_related("role")
        return Response(UserRoleSerializer(user_roles, many=True).data)

    @require_admin
    def post(self, request, user_id):
        target = self._get_user(user_id)
        if not target:
            return Response({"detail": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserRoleAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        role = Role.objects.get(id=serializer.validated_data["role_id"])
        _, created = UserRole.objects.get_or_create(user=target, role=role)
        if not created:
            return Response(
                {"detail": "Эта роль уже назначена пользователю."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({"detail": f"Роль '{role.name}' назначена."}, status=status.HTTP_201_CREATED)


class UserRoleDeleteView(APIView):
    @require_admin
    def delete(self, request, user_id, role_id):
        deleted, _ = UserRole.objects.filter(
            user_id=user_id, role_id=role_id
        ).delete()
        if not deleted:
            return Response({"detail": "Связь не найдена."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
