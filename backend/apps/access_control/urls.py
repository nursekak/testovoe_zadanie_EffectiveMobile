from django.urls import path
from .views import (
    RoleListView,
    RoleDetailView,
    PermissionListView,
    PermissionDetailView,
    RolePermissionsView,
    RolePermissionDeleteView,
    UserRolesView,
    UserRoleDeleteView,
)

urlpatterns = [
    path("roles/", RoleListView.as_view(), name="admin-roles"),
    path("roles/<uuid:pk>/", RoleDetailView.as_view(), name="admin-role-detail"),
    path("roles/<uuid:pk>/permissions/", RolePermissionsView.as_view(), name="admin-role-permissions"),
    path("roles/<uuid:pk>/permissions/<uuid:perm_id>/", RolePermissionDeleteView.as_view(), name="admin-role-permission-delete"),
    path("permissions/", PermissionListView.as_view(), name="admin-permissions"),
    path("permissions/<uuid:pk>/", PermissionDetailView.as_view(), name="admin-permission-detail"),
    path("users/<uuid:user_id>/roles/", UserRolesView.as_view(), name="admin-user-roles"),
    path("users/<uuid:user_id>/roles/<uuid:role_id>/", UserRoleDeleteView.as_view(), name="admin-user-role-delete"),
]
