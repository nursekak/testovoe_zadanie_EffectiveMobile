from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    middle_name = serializers.CharField(max_length=150, required=False, default="")

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
