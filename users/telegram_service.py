import requests
from django.conf import settings
from celery import shared_task


class TelegramService:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, chat_id, message):
        """Отправка сообщения в Telegram"""
        url = f"{self.base_url}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Ошибка отправки сообщения в Telegram: {e}")
            return False

    def get_bot_info(self):
        """Получение информации о боте"""
        url = f"{self.base_url}/getMe"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка получения информации о боте: {e}")
            return None

    def set_webhook(self, webhook_url):
        """Установка webhook для бота"""
        url = f"{self.base_url}/setWebhook"

        payload = {
            'url': webhook_url
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка установки webhook: {e}")
            return None


@shared_task
def send_telegram_notification(chat_id, message):
    """Асинхронная отправка сообщения в Telegram"""
    service = TelegramService()
    return service.send_message(chat_id, message)


@shared_task
def send_habit_reminder(habit_id):
    """Отправка напоминания о привычке"""
    from habit.models import Habit

    try:
        habit = Habit.objects.get(id=habit_id)
        user = habit.user

        if not user.is_telegram_connected or not user.telegram_chat_id:
            return

        message = (
            f"🔔 Напоминание о привычке!\n\n"
            f"💪 <b>{habit.action}</b>\n"
            f"⏰ Время: {habit.time.strftime('%H:%M')}\n"
            f"📍 Место: {habit.place}\n"
            f"⏱️ Время на выполнение: {habit.time_to_complete} сек.\n\n"
        )

        if habit.reward:
            message += f"🎁 Вознаграждение: {habit.reward}"
        elif habit.related_habit:
            message += f"➡️ Следующая привычка: {habit.related_habit.action}"

        send_telegram_notification.delay(user.telegram_chat_id, message)

    except Habit.DoesNotExist:
        pass