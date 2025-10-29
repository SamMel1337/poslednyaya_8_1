from users.models import TelegramUser
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.paginator import Paginator
from models import Habit, HabitTracking
from serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    HabitSerializer,
    PublicHabitSerializer,
    HabitTrackingSerializer,
    TelegramUserSerializer,
)
from .permissions import IsOwner
from .tasks import send_telegram_reminder


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@method_decorator(cache_page(60 * 15), name="dispatch")  # Кеширование на 15 минут
class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Инвалидируем кеш связанных данных
            cache.delete_pattern("habits_*")
            cache.delete_pattern("user_*")
            return Response(
                {
                    "message": "Пользователь успешно зарегистрирован",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        cache_key = f"habits_user_{self.request.user.id}"
        queryset = cache.get(cache_key)

        if not queryset:
            queryset = Habit.objects.filter(user=self.request.user).select_related(
                "user"
            )
            cache.set(cache_key, queryset, 60 * 15)  # Кешируем на 15 минут

        return queryset

    def perform_create(self, serializer):
        habit = serializer.save(user=self.request.user)
        # Инвалидируем кеш привычек пользователя
        cache.delete(f"habits_user_{self.request.user.id}")
        cache.delete_pattern("public_habits_*")

        # Создаем задачу для напоминания
        send_telegram_reminder.delay(habit.id)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        # Инвалидируем кеш при обновлении
        cache.delete(f"habits_user_{self.request.user.id}")
        cache.delete_pattern("public_habits_*")

    def perform_destroy(self, instance):
        # Инвалидируем кеш перед удалением
        cache.delete(f"habits_user_{self.request.user.id}")
        cache.delete_pattern("public_habits_*")
        super().perform_destroy(instance)

    @method_decorator(cache_page(60 * 15))  # Кеширование публичных привычек на 15 минут
    @action(detail=False, methods=["get"])
    def public(self, request):
        page_number = request.query_params.get("page", 1)
        cache_key = f"public_habits_page_{page_number}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        habits = Habit.objects.filter(is_public=True).select_related("user")

        # Пагинация
        paginator = Paginator(habits, 5)
        page_obj = paginator.get_page(page_number)

        serializer = PublicHabitSerializer(page_obj, many=True)

        response_data = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page_obj.number,
            "results": serializer.data,
        }

        # Кешируем результат
        cache.set(cache_key, response_data, 60 * 15)

        return Response(response_data)


class HabitTrackingViewSet(viewsets.ModelViewSet):
    serializer_class = HabitTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        cache_key = f"habit_tracking_user_{self.request.user.id}"
        queryset = cache.get(cache_key)

        if not queryset:
            queryset = HabitTracking.objects.filter(
                habit__user=self.request.user
            ).select_related("habit")
            cache.set(cache_key, queryset, 60 * 15)  # Кешируем на 15 минут

        return queryset

    def perform_create(self, serializer):
        # Инвалидируем кеш трекинга и привычек
        cache.delete(f"habit_tracking_user_{self.request.user.id}")
        cache.delete(f"habits_user_{self.request.user.id}")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        cache.delete(f"habit_tracking_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        cache.delete(f"habit_tracking_user_{self.request.user.id}")
        super().perform_destroy(instance)


class TelegramUserViewSet(viewsets.ModelViewSet):
    serializer_class = TelegramUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        cache_key = f"telegram_user_{self.request.user.id}"
        queryset = cache.get(cache_key)

        if not queryset:
            queryset = TelegramUser.objects.filter(user=self.request.user)
            cache.set(cache_key, queryset, 60 * 60)  # Кешируем на 1 час

        return queryset

    def perform_create(self, serializer):
        # Инвалидируем кеш
        cache.delete(f"telegram_user_{self.request.user.id}")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        cache.delete(f"telegram_user_{self.request.user.id}")

    def perform_destroy(self, instance):
        cache.delete(f"telegram_user_{self.request.user.id}")
        super().perform_destroy(instance)
