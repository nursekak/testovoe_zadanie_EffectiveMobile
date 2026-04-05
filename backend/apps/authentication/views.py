from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer, LoginSerializer, RefreshSerializer, LogoutSerializer
from .services import generate_access_token, generate_refresh_token, rotate_refresh_token, revoke_refresh_token
from apps.users.serializers import UserProfileSerializer

User = get_user_model()


class RegisterView(APIView):
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
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_token = serializer.validated_data["refresh_token"]
        revoke_refresh_token(raw_token)
        return Response({"detail": "Вы вышли из системы."})
