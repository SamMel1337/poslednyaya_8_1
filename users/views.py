from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from habit.models import HabitTracking
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    TelegramConnectionSerializer,
)
from telegram_service import TelegramService


class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Пользователь успешно зарегистрирован",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "Успешный вход",
                    "user": UserProfileSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class TelegramConnectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TelegramConnectionSerializer(
            data=request.data, context={"user": request.user}
        )

        if serializer.is_valid():
            user = request.user
            telegram_chat_id = serializer.validated_data["telegram_chat_id"]

            # Сохраняем chat_id пользователя
            user.telegram_chat_id = telegram_chat_id
            user.is_telegram_connected = True
            user.save()

            # Отправляем приветственное сообщение через Telegram
            telegram_service = TelegramService()
            message = (
                f"🎉 Отлично! Ваш аккаунт успешно подключен к боту привычек.\n\n"
                f"👤 Пользователь: {user.username}\n"
                f"📧 Email: {user.email}\n\n"
                f"Теперь вы будете получать напоминания о своих привычках!"
            )

            success = telegram_service.send_message(telegram_chat_id, message)

            if success:
                return Response(
                    {
                        "message": "Telegram успешно подключен",
                        "telegram_chat_id": telegram_chat_id,
                        "is_telegram_connected": True,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "error": "Не удалось отправить тестовое сообщение. Проверьте chat_id."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TelegramDisconnectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.telegram_chat_id:
            # Отправляем сообщение о отключении
            telegram_service = TelegramService()
            message = "🔕 Уведомления о привычках отключены. Вы больше не будете получать напоминания."
            telegram_service.send_message(user.telegram_chat_id, message)

        # Отключаем Telegram
        user.telegram_chat_id = None
        user.is_telegram_connected = False
        user.save()

        return Response(
            {"message": "Telegram успешно отключен", "is_telegram_connected": False},
            status=status.HTTP_200_OK,
        )


class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response(
                {"message": "Успешный выход из системы"}, status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"error": "Не удалось выйти из системы"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def user_habits_stats(request):
    """Статистика привычек пользователя"""

    user = request.user
    habits = user.habits.all()
    completed_count = HabitTracking.objects.filter(
        habit__user=user, is_completed=True
    ).count()

    return Response(
        {
            "total_habits": habits.count(),
            "public_habits": habits.filter(is_public=True).count(),
            "pleasant_habits": habits.filter(is_pleasant=True).count(),
            "completed_actions": completed_count,
            "is_telegram_connected": user.is_telegram_connected,
        }
    )
