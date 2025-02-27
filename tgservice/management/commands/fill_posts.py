from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from telethon.sync import TelegramClient
from tgservice.models import Channel, Message
from django.conf import settings
from telethon.errors import FloodWaitError, UsernameInvalidError, InvalidBufferError
import time

# Загружаем API_ID и API_HASH из .env
API_ID, API_HASH = settings.API_ID, settings.API_HASH
API_ID_1, API_HASH_1 = settings.API_ID_1, settings.API_HASH_1
SESSION_NAME = "session_name"

# Инициализация Telethon клиента
client = TelegramClient(SESSION_NAME, API_ID_1, API_HASH_1)

class Command(BaseCommand):
    help = "Парсит последние сообщения из каналов, сохранённых в БД"

    def fetch_and_save_messages(self, client, channel: Channel, limit: int = 30):
        """Парсит сообщения и сохраняет их в БД."""
        retries = 5  # Количество повторных попыток
        wait_time = 10  # Задержка перед повтором
        
        for attempt in range(retries):
            try:
                messages = client.get_messages(channel.name, limit=limit)
                new_or_updated = 0

                for msg in messages:
                    message_obj, created = Message.objects.update_or_create(
                        channel=channel,
                        date=msg.date,
                        defaults={
                            "text": msg.text or "",
                            "views": msg.views or 0,
                            "reactions": sum(r.count for r in msg.reactions.results) if msg.reactions else 0,
                            "reposts": msg.forwards or 0,
                        }
                    )
                    if created:
                        new_or_updated += 1

                    time.sleep(1)  # Задержка в 1 сек, чтобы избежать блокировки

                return new_or_updated
            
            except FloodWaitError as e:
                print(f"⚠ FloodWaitError: Telegram требует подождать {e.seconds} сек.")
                time.sleep(e.seconds)
            except InvalidBufferError:
                print(f"❌ InvalidBufferError: Слишком много запросов. Ждём {wait_time} сек...")
                time.sleep(wait_time)
                wait_time *= 2  # Удваиваем задержку перед следующей попыткой
            except UsernameInvalidError:
                print(f"❌ Ошибка: канал {channel.name} недоступен. Пропускаем его.")
                return 0
            except Exception as e:
                print(f"⚠ Попытка {attempt + 1}: ошибка {e}. Ждём {wait_time} сек и повторяем...")
                time.sleep(wait_time)

        print(f"❌ Ошибка: канал {channel.name} не обработан после {retries} попыток.")
        return 0

    def handle(self, *args, **options):
        """Запуск команды"""
        # channels = Channel.objects.all()  # Берём все каналы из БД
        channels = Channel.objects.annotate(
                msg_count=Count("messages", distinct=True) # DISTINCT нужен для корректного подсчёта сообщений в Message
            ).filter(Q(msg_count__lt=30) | Q(msg_count=0)) # Оставить те каналы, у кого сообщений либо = 0 или <30
        
        if not channels.exists():
            self.stdout.write(self.style.WARNING("⚠ В базе нет каналов для парсинга"))
            return

        self.stdout.write(self.style.NOTICE(f"🔄 Начинаем парсинг сообщений для {channels.count()} каналов..."))

        # Используем клиент в контекстном менеджере, чтобы он корректно работал!
        with TelegramClient(SESSION_NAME, API_ID, API_HASH).start() as client:
            for channel in channels:
                new_or_updated = self.fetch_and_save_messages(client, channel)
                self.stdout.write(self.style.SUCCESS(f"✔ {channel.name}: добавлено/обновлено {new_or_updated} сообщений"))

                time.sleep(10)  # Задержка перед следующим каналом

        self.stdout.write(self.style.SUCCESS("✅ Парсинг сообщений завершён"))