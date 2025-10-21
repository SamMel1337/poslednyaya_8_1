from django.core.management.base import BaseCommand
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup Telegram bot webhook'

    def handle(self, *args, **options):
        bot_token = settings.TELEGRAM_BOT_TOKEN
        webhook_url = "https://yourdomain.com/api/telegram/webhook/"

        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        payload = {
            'url': webhook_url
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            self.stdout.write(
                self.style.SUCCESS('Webhook успешно установлен')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Ошибка при установке webhook')
            )