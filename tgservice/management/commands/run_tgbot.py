from django.core.management.base import BaseCommand
from tgservice.tgbot.main import start_bot
import asyncio

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **kwargs):
        asyncio.run(start_bot())