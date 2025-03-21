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
SESSION_ONE = "session_one"

# Инициализация Telethon клиента
client_one = TelegramClient(SESSION_NAME, API_ID, API_HASH)
client_two = TelegramClient(SESSION_ONE, API_ID_1, API_HASH_1)

class Command(BaseCommand):
    help = "Парсит последние сообщения из каналов, сохранённых в БД"

    def fetch_and_save_messages(self, client, channel: Channel, limit: int = 30):
        """Парсит сообщения и сохраняет их в БД."""
        retries = 3  # Количество повторных попыток
        wait_time = 3  # Задержка перед повтором
        
        for attempt in range(retries):
            try:
                messages = client.get_messages(channel.name, limit=limit)
                new_or_updated = 0

                for msg in messages:
                    mes_obj, created = Message.objects.update_or_create(
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
                raise  # Вместо return -1, просто пробрасываем ошибку выше
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
        channels = Channel.objects.annotate(
                msg_count=Count("messages", distinct=True) # DISTINCT нужен для корректного подсчёта сообщений в Message
            ).filter(msg_count__lte=25).exclude(category__name__in=[                    # Оставить те каналы, у кого сообщений <=20
                    "SMM - social media", "Авто, мото,  техника", "Бизнес и стартапы",
                    "Блоги", "Для родителей", "ЕГЭ, ОГЭ, Экзамены", "Здоровье и спорт", 
                    "Инвестиции и финансы", "Маркетинг и реклама", "Маркетплейсы", 
                    "Медицина", "Наука и образование", "Недвижимость", "Психология",
                    "Путешествия", "Развитие, обучение", "Рукоделие и хобби", "Строительство и Ремонт",
                    "Фильмы и Сериалы"]).distinct() # Убираем категории, где сообщений уже много
        
        # Проверим категории каналов, которые попали в выборку
        categories_in_selection = sorted(set(ch.category.name for ch in channels))
        for category in categories_in_selection:
            print("Категория:", category)

        if not channels.exists():
            self.stdout.write(self.style.WARNING("⚠ В базе нет каналов для парсинга"))
            return

        self.stdout.write(self.style.NOTICE(f"🔄 Начинаем парсинг сообщений для {channels.count()} каналов..."))

        clients = [client_one, client_two]
        client_index = 0

        # Запускаем всех клиентов
        for client in clients:
            if not client.is_connected():
                client.connect()  # Подключение (если сессия уже есть) 
        
        # Храним время ожидания для каждого клиента
        client_wait_times = {i: 0 for i in range(len(clients))}

        for channel in channels:
            while True:  # Повторяем до успешного выполнения
                try:
                    new_or_updated = self.fetch_and_save_messages(clients[client_index], channel)                   
                    self.stdout.write(self.style.SUCCESS(f"✔ {channel.name}: добавлено/обновлено {new_or_updated} сообщений"))
                    
                    client_wait_times[client_index] = 0 # Сбрасываем время ожидания для текущего клиента
                    break  # Выходим из while, переходим к следующему каналу

                except FloodWaitError as e:
                    wait_time = e.seconds  
                    print(f"⚠ FloodWaitError у {clients[client_index].session.filename}, ждём {wait_time} сек.")

                    # Запоминаем, что этот клиент получил FloodWaitError
                    client_wait_times[client_index] = wait_time

                    # Ищем клиента, у которого **нет** FloodWaitError
                    available_clients = [i for i, t in client_wait_times.items() if t == 0]

                    if available_clients:  
                        next_client_index = available_clients[0]  
                        print(f"🔄 Переключаемся на {clients[next_client_index].session.filename}")
                        client_index = next_client_index  
                        if not clients[client_index].is_connected():
                            clients[client_index].connect()
                    else:
                        # Все клиенты в FloodWait → ждём **минимальное** время
                        min_wait = min(client_wait_times.values())
                        print(f"⚠ Оба клиента в FloodWait! Ожидаем {min_wait} сек...")
                        time.sleep(min_wait)
                        # После ожидания уменьшаем таймер у всех клиентов
                        for i in client_wait_times:
                            client_wait_times[i] = max(0, client_wait_times[i] - min_wait)
                
                except Exception as e:
                    print(f"❌ Неизвестная ошибка: {e}")
                    break  

            time.sleep(1)  # Задержка перед следующим каналом

        self.stdout.write(self.style.SUCCESS("✅ Парсинг сообщений завершён"))