from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    UserUpdateView,
    UserLogoutView,
    TelegramConnectView,
    TelegramDisconnectView,
    user_habits_stats
)

urlpatterns = [
    # Аутентификация
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),

    # Профиль
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UserUpdateView.as_view(), name='user-update'),

    # Telegram
    path('telegram/connect/', TelegramConnectView.as_view(), name='telegram-connect'),
    path('telegram/disconnect/', TelegramDisconnectView.as_view(), name='telegram-disconnect'),

    # Статистика
    path('stats/', user_habits_stats, name='user-stats'),
]