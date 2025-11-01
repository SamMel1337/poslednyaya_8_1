from celery import shared_task
import requests
from django.utils import timezone
from django.conf import settings
from users.models import TelegramUser
from .models import Habit


@shared_task
def send_telegram_reminder(habit_id):
    try:
        habit = Habit.objects.get(id=habit_id)
        telegram_user = TelegramUser.objects.filter(
            user=habit.user, is_active=True
        ).first()

        if not telegram_user:
            return

        message = (
            f"🔔 Напоминание о привычке!\n\n"
            f"Привычка: {habit.action}\n"
            f"Время: {habit.time}\n"
            f"Место: {habit.place}\n"
            f"Время на выполнение: {habit.time_to_complete} сек."
        )

        send_telegram_message(telegram_user.telegram_chat_id, message)

    except Habit.DoesNotExist:
        pass


@shared_task
def send_daily_reminders():
    today = timezone.now().date()
    habits = Habit.objects.filter(user__telegram__is_active=True).select_related("user")

    for habit in habits:
        # Проверяем, нужно ли отправлять напоминание сегодня
        days_since_creation = (today - habit.created_at.date()).days
        if days_since_creation % habit.periodicity == 0:
            send_telegram_reminder.delay(habit.id)


def send_telegram_message(chat_id, message):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False
