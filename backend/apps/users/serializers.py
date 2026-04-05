from rest_framework import serializers
from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "middle_name",
            "full_name",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "is_active", "created_at", "updated_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "middle_name"]

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Имя не может быть пустым.")
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Фамилия не может быть пустой.")
        return value
