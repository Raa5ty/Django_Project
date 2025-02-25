from django.core.management.base import BaseCommand
from telethon import TelegramClient
from tgservice.models import Channel, Message
from django.utils.timezone import make_aware
from django.conf import settings
import asyncio
import os

# Загружаем API_ID и API_HASH из .env
API_ID = settings.API_ID
API_HASH = settings.API_HASH
SESSION_NAME = "session_name"

# Инициализация Telethon клиента
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

class Command(BaseCommand):
    help = "Парсит последние сообщения из каналов, сохранённых в БД"

    async def fetch_and_save_messages(self, channel: Channel, limit: int = 30):
        """Парсит сообщения и сохраняет их в БД."""
        async with client:
            messages = await client.get_messages(channel.name, limit=limit)

            for msg in messages:
                message_obj = Message.objects.create(
                    channel=channel,
                    date=make_aware(msg.date),
                    text=msg.text or "",
                    views=msg.views or 0,
                    reactions=sum(r.count for r in msg.reactions.results) if msg.reactions else 0,
                    reposts=msg.forwards or 0,
                )
                self.stdout.write(self.style.SUCCESS(f"✔ Добавлено сообщение ID {message_obj.id} из {channel.name}"))

    def handle(self, *args, **options):
        """Запуск команды"""
        channels = Channel.objects.all()  # Берём все каналы из БД
        if not channels.exists():
            self.stdout.write(self.style.WARNING("⚠ В базе нет каналов для парсинга"))
            return

        self.stdout.write(self.style.NOTICE(f"🔄 Начинаем парсинг сообщений для {channels.count()} каналов..."))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for channel in channels:
            loop.run_until_complete(self.fetch_and_save_messages(channel))

        loop.close()
        self.stdout.write(self.style.SUCCESS("✅ Парсинг сообщений завершён"))