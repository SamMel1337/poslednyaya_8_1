from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView,
    HabitViewSet,
    HabitTrackingViewSet,
    TelegramUserViewSet,
    CustomTokenObtainPairView
)

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habits')
router.register(r'tracking', HabitTrackingViewSet, basename='tracking')
router.register(r'telegram', TelegramUserViewSet, basename='telegram')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
]