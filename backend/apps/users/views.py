from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserProfileSerializer, UserUpdateSerializer
from apps.authentication.utils import require_authenticated


class MeView(APIView):
    @require_authenticated
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @require_authenticated
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)

    @require_authenticated
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])

        from apps.authentication.models import RefreshToken
        RefreshToken.objects.filter(user=user, revoked=False).update(revoked=True)

        return Response(
            {"detail": "Аккаунт деактивирован. До свидания."},
            status=status.HTTP_200_OK,
        )
