from django.urls import path, include

urlpatterns = [
    path("api/auth/", include("apps.authentication.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/admin/", include("apps.access_control.urls")),
    path("api/business/", include("apps.business.urls")),
]
