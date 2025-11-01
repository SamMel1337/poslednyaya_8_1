from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=6, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "telegram_chat_id",
            "phone",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Пароли не совпадают"}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Неверные учетные данные")
            if not user.is_active:
                raise serializers.ValidationError("Аккаунт неактивен")
            attrs["user"] = user
            return attrs
        raise serializers.ValidationError("Необходимо указать username и password")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "telegram_chat_id",
            "phone",
            "is_telegram_connected",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined", "is_telegram_connected")


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "telegram_chat_id", "phone")


class TelegramConnectionSerializer(serializers.Serializer):
    telegram_chat_id = serializers.IntegerField()

    def validate_telegram_chat_id(self, value):
        if (
            User.objects.filter(telegram_chat_id=value)
            .exclude(id=self.context["user"].id)
            .exists()
        ):
            raise serializers.ValidationError(
                "Этот Telegram ID уже используется другим пользователем"
            )
        return value
