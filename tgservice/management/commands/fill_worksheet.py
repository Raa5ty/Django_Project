from django.core.management.base import BaseCommand
from tgservice.models import Channel, Message, WorkSheet
from datetime import timedelta
import re

class Command(BaseCommand):
    help = 'Заполнение рабочей таблицы WorkSheet с данными о каналах и сообщениях'

    @staticmethod
    def clean_text(text):
        # Удаляем все ссылки
        text = re.sub(r'http\S+', '', text)
        # Удаляем все символы, которые не являются буквами, цифрами или пробелами (например, спецсимволы)
        text = re.sub(r'[^a-zA-Zа-яА-Я0-9\s]', '', text)
        # Убираем лишние пробелы (два и более пробела заменяем на один)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def handle(self, *args, **kwargs):
        # Получаем все каналы
        channels = Channel.objects.all()

        for channel in channels:
            # Собираем все сообщения канала
            messages = Message.objects.filter(channel=channel, text__gt='').order_by('-date')
            
            # Собираем текст всех сообщений в одну строку, начиная с последних
            text_messages = ''
            text_length = 0
            for message in messages:
                message_text = self.clean_text(message.text.strip()) + '\n'  # Добавляем новую строку для разделения сообщений
                text_length += len(message_text)
                text_messages = message_text + text_messages  # Добавляем к началу строки
                if text_length >= 15000:
                    break  # Если текст достиг лимита, останавливаем добавление

            # Получаем дату первого и последнего поста
            first_post_date = messages.last().date if messages else None
            last_post_date = messages.first().date if messages else None

            # Количество активных месяцев
            active_months = (last_post_date - first_post_date).days // 30 if first_post_date and last_post_date else 0

            # Общее количество постов
            total_posts = messages.count()

            # Добавляем или обновляем запись в рабочей таблице
            WorkSheet.objects.update_or_create(
                channel_name=channel.name,
                defaults={
                    'category': channel.category.name,
                    'subscribers': channel.subscribers,
                    'title': channel.title,
                    'description': channel.description,
                    'text_messages': text_messages,
                    'text_length': text_length,
                    'first_post_date': first_post_date,
                    'last_post_date': last_post_date,
                    'total_posts': total_posts,
                    'active_months': active_months,
                    'profile_channel': None,
                    'profile_intokens': None,
                    'profile_outtokens': None,
                    'keywords_channel': None,
                    'keywords_intokens': None,
                    'keywords_outtokens': None,           
                }
            )

        self.stdout.write(self.style.SUCCESS('Рабочая таблица WorkSheet успешно заполнена.'))
