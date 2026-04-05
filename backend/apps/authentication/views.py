from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import RegisterSerializer, LoginSerializer, RefreshSerializer, LogoutSerializer
from .services import generate_access_token, generate_refresh_token, rotate_refresh_token, revoke_refresh_token
from apps.users.serializers import UserProfileSerializer

User = get_user_model()


class RegisterView(APIView):
    @extend_schema(
        tags=["auth"],
        summary="Регистрация нового пользователя",
        request=RegisterSerializer,
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        access = generate_access_token(user)
        refresh = generate_refresh_token(user)
        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "access_token": access,
                "refresh_token": refresh,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    @extend_schema(
        tags=["auth"],
        summary="Вход в систему (получить JWT-токены)",
        request=LoginSerializer,
        examples=[
            OpenApiExample("admin", value={"email": "admin@example.com", "password": "Test1234!"}),
            OpenApiExample("manager", value={"email": "manager@example.com", "password": "Test1234!"}),
            OpenApiExample("viewer", value={"email": "viewer@example.com", "password": "Test1234!"}),
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Неверный email или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Неверный email или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Аккаунт деактивирован."},
                status=status.HTTP_403_FORBIDDEN,
            )

        access = generate_access_token(user)
        refresh = generate_refresh_token(user)
        return Response(
            {
                "user": UserProfileSerializer(user).data,
                "access_token": access,
                "refresh_token": refresh,
            }
        )


class RefreshView(APIView):
    @extend_schema(tags=["auth"], summary="Обновить access-токен по refresh-токену", request=RefreshSerializer)
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_token = serializer.validated_data["refresh_token"]
        try:
            user, new_access, new_refresh = rotate_refresh_token(raw_token)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"access_token": new_access, "refresh_token": new_refresh})


class LogoutView(APIView):
    @extend_schema(tags=["auth"], summary="Выход из системы (отозвать refresh-токен)", request=LogoutSerializer)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_token = serializer.validated_data["refresh_token"]
        revoke_refresh_token(raw_token)
        return Response({"detail": "Вы вышли из системы."})
