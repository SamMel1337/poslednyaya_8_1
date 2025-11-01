import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import User
from telegram_service import TelegramService


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Webhook для обработки сообщений от Telegram бота"""
    try:
        data = json.loads(request.body)
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()

        if not chat_id:
            return JsonResponse({"status": "error", "message": "No chat id"})

        telegram_service = TelegramService()

        # Обработка команд
        if text == "/start":
            welcome_message = (
                "👋 Добро пожаловать в бот для отслеживания привычек!\n\n"
                "Чтобы подключить бота к вашему аккаунту:\n"
                "1. Перейдите в настройки профиля в веб-приложении\n"
                "2. Введите этот ID в поле подключения Telegram: \n"
                f"<code>{chat_id}</code>\n\n"
                "После этого вы будете получать напоминания о ваших привычках!"
            )
            telegram_service.send_message(chat_id, welcome_message)

        elif text == "/help":
            help_message = (
                "📋 Доступные команды:\n\n"
                "/start - Начало работы с ботом\n"
                "/help - Получить справку\n"
                "/status - Проверить статус подключения\n"
                "\n"
                "Для управления привычками используйте веб-приложение."
            )
            telegram_service.send_message(chat_id, help_message)

        elif text == "/status":
            # Проверяем, подключен ли пользователь
            try:
                user = User.objects.get(telegram_chat_id=chat_id)
                status_message = (
                    f"✅ Ваш аккаунт подключен!\n\n"
                    f"👤 Пользователь: {user.username}\n"
                    f"📧 Email: {user.email}\n"
                    f"🔔 Уведомления: {'Включены' if user.is_telegram_connected else 'Отключены'}"
                )
            except User.DoesNotExist:
                status_message = (
                    "❌ Ваш аккаунт не подключен.\n\n"
                    "Чтобы подключить бота:\n"
                    "1. Перейдите в настройки профиля в веб-приложении\n"
                    "2. Введите этот ID: \n"
                    f"<code>{chat_id}</code>"
                )
            telegram_service.send_message(chat_id, status_message)

        else:
            # Ответ на неизвестные сообщения
            unknown_message = (
                "🤔 Я не понимаю эту команду.\n\n"
                "Используйте /help для получения списка доступных команд."
            )
            telegram_service.send_message(chat_id, unknown_message)

        return JsonResponse({"status": "ok"})

    except Exception as e:
        print(f"Error in telegram webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)})


def setup_webhook(request):
    """Установка webhook для Telegram бота"""
    if not settings.DEBUG:
        return JsonResponse({"error": "Only available in debug mode"})

    webhook_url = "https://yourdomain.com/api/users/telegram/webhook/"
    telegram_service = TelegramService()
    result = telegram_service.set_webhook(webhook_url)

    return JsonResponse({"status": "webhook set", "result": result})
