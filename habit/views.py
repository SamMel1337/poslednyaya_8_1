from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Habit, HabitTracking
from .serializers import (
    UserRegistrationSerializer,
    HabitSerializer,
    PublicHabitSerializer,
    HabitTrackingSerializer,
    TelegramUserSerializer,
    UserSerializer
)
from .permissions import IsOwner
from .tasks import send_telegram_reminder


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Пользователь успешно зарегистрирован',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        habit = serializer.save()
        # Создаем задачу для напоминания
        send_telegram_reminder.delay(habit.id)

    @action(detail=False, methods=['get'])
    def public(self, request):
        habits = Habit.objects.filter(is_public=True)

        # Пагинация
        page_number = request.query_params.get('page', 1)
        paginator = Paginator(habits, 5)
        page_obj = paginator.get_page(page_number)

        serializer = PublicHabitSerializer(page_obj, many=True)
        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'results': serializer.data
        })


class HabitTrackingViewSet(viewsets.ModelViewSet):
    serializer_class = HabitTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HabitTracking.objects.filter(habit__user=self.request.user)


class TelegramUserViewSet(viewsets.ModelViewSet):
    serializer_class = TelegramUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TelegramUser.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)