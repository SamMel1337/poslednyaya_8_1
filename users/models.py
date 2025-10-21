from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    telegram_chat_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        verbose_name='ID чата в Telegram'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class TelegramUser(models.Model):
    """Базовая модель пользователя Telegram"""
    telegram_id = models.BigIntegerField(
        unique=True,
        verbose_name="ID в Telegram"
    )
    username = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Юзернейм"
    )
    first_name = models.CharField(
        max_length=64,
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Фамилия"
    )
    language_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Язык"
    )
    is_bot = models.BooleanField(
        default=False,
        verbose_name="Бот"
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name="Премиум"
    )

    # Дополнительные поля
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Последнее обновление"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"
        db_table = "telegram_users"

    def __str__(self):
        return f"@{self.username}" if self.username else f"{self.first_name} (ID: {self.telegram_id})"

    def get_full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name