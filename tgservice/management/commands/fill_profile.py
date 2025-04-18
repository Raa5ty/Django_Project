from django.core.management.base import BaseCommand
from tgservice.prompts import system_profile, user_profile
from tgservice.models import WorkSheet
from openai import OpenAI
from datetime import timedelta
from django.conf import settings
import json
import time
import re
import os

api_key = settings.OPENAI_API_KEY

class Command(BaseCommand):
    help = 'Профилирует каналы через OpenAI Batch API'

    def handle(self, *args, **options):
        # 1. Проверка наличия папки для результатов или её создание
        self.results_dir = os.path.join(settings.BASE_DIR, "tgservice", "results_fill_db")
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            print(f"Папка {self.results_dir} успешно создана.")
        else:
            print(f"Папка {self.results_dir} уже существует.")

        # 2. Сбор данных и создание JSONL
        input_file = self.create_jsonl()
        if input_file is None:
            print("✅ Все каналы уже прошли профилирование.")
            return

        # 3. Отправка в Batch API
        result_file = self.process_batch_split(input_file)
        if result_file is None:
            print("Ошибка при обработке batch-запроса. Завершаем выполнение.")
            return

        # 4. Сохранение результата в БД
        self.update_db(result_file)

    def clean_text(self, text):
        """Удаляет лишние пробелы и ссылки из текста."""
        text = re.sub(r'http\S+', '', text)
        return ' '.join(text.split())

    def create_jsonl(self):
        """Создаёт JSONL файл для отправки в OpenAI API."""
        system_prompt = system_profile  # Мы всегда работаем с профилем
        user_prompt = user_profile

        # Делаем запрос к базе данных с помощью Django ORM
        worksheets = WorkSheet.objects.filter(profile_channel=None)
        total = worksheets.count()

        if total == 0:
            return None

        json_profiles = []

        for worksheet in worksheets:
            title = self.clean_text(worksheet.title) if worksheet.title else ''
            description = self.clean_text(worksheet.description) if worksheet.description else ''
            text_messages = self.clean_text(worksheet.text_messages) if worksheet.text_messages else ''

            text_content = "\n".join(filter(None, [worksheet.category, title, description, text_messages]))
            full_user_prompt = f'{user_prompt}\n{text_content}'

            json_profile = {
                "custom_id": worksheet.channel_name,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",  # Модель можно передавать как параметр
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_user_prompt}
                    ],
                    "max_tokens": 1000
                }
            }
            json_profiles.append(json_profile)

        # Путь к файлу
        file_path = os.path.join(self.results_dir, "get_profile.jsonl")

        # Записываем список в файл в формате jsonl
        with open(file_path, 'w', encoding='utf-8') as json_file:
            for profile in json_profiles:
                json.dump(profile, json_file, ensure_ascii=False)
                json_file.write("\n")  # Каждая запись на новой строке

        print(f"📄 JSONL-файл создан: {file_path}")
        print(f"📌 Каналов для профилирования: {total}")

        # Возвращаем путь к файлу
        return file_path
        
    def process_batch_split(self, input_file, max_lines=250, endpoint="/v1/chat/completions", completion_window="24h"):
        """Обработка batch-запроса с разбиением входного файла на части."""
        base_name = os.path.basename(input_file).split('.')[0]
        result_file_name = os.path.basename(input_file).replace("get_", "result_", 1)  # "result_profile.jsonl"
        result_file_path = os.path.join(self.results_dir, result_file_name)

        # Валидация JSON по строкам
        with open(input_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                try:
                    json.loads(line)
                except Exception as e:
                    print(f"[!] Ошибка в строке {i}: {e}")

        # Проверка наличия строк в файле
        with open(input_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        total_lines = len(lines)
        if total_lines == 0:
            print("Входной файл пуст.")
            return None
        total_parts = (total_lines + max_lines - 1) // max_lines
        # Если строк меньше, чем max_lines, не делим на части
        if total_lines <= max_lines:
            print(f"Файл содержит всего {total_lines} строк, будет обработан целиком, файл: {input_file}")
            parts = [input_file]  # Просто обрабатываем один файл, добавляем в список один файл input_file
        else:
            # Разбиение на части. Если строк больше, чем max_lines, делим на части
            parts = []
            for i in range(0, total_lines, max_lines):
                part_name = os.path.join(self.results_dir, f"{base_name}_part{(i // max_lines) + 1}.jsonl") # Путь для части
                print(f"Создана {i // max_lines + 1} часть файла из {total_parts}, по пути: {part_name}")
                with open(part_name, "w", encoding="utf-8") as part_file:
                    part_file.writelines(lines[i:i + max_lines])
                parts.append(part_name)

            print(f"Входной файл насчитывает {total_lines} строк и будет разбит на {len(parts)} частей.")

        # Обработка каждой части
        client = OpenAI(api_key=api_key)  # Инициализация клиента OpenAI
        # Создание списка для результато
        result_parts = []

        for idx, part in enumerate(parts):
            print(f"Обрабатывается часть {idx + 1} из {len(parts)}, файл: {part}")

            with open(part, "rb") as file:
                uploaded_file = client.files.create(file=file, purpose="batch")
                print(f"Файл загружен. ID: {uploaded_file.id}")

            batch_job = client.batches.create(input_file_id=uploaded_file.id, endpoint=endpoint, completion_window=completion_window)

            while batch_job.status not in ["completed", "failed", "cancelled", "expired"]:
                time.sleep(30)  # Ожидание перед повторной проверкой статуса
                print(f"Статус batch-запроса: {batch_job.status}... повторная попытка через 30 секунд...")
                batch_job = client.batches.retrieve(batch_job.id)

            if batch_job.status in ["completed", "expired"]:
                result_file_id = batch_job.output_file_id
                result = client.files.content(result_file_id).content

                # Временный файл для результатов
                part_result_file = os.path.join(self.results_dir, f"results_{os.path.basename(part)}") # Получаем путь к части {part}
                print(f"Результаты записаны в файл: {part_result_file}")
                with open(part_result_file, "wb") as file:
                    file.write(result)
                result_parts.append(part_result_file)

                start_idx = idx * max_lines
                end_idx = min(start_idx + max_lines, total_lines)
                print(f"Часть {idx + 1} с {end_idx - start_idx} строками завершена.")

            elif batch_job.status in ["failed", "cancelled"]:
                print(f"[!] Batch-запрос для части {idx + 1} завершился неудачей: статус — {batch_job.status}")
                # Если хоть что-то успело сохраниться — продолжаем, иначе возвращаем None
                if not result_parts:
                    print("[!] Ни одна из частей не отработала. Итоговый файл не будет создан.")
                    return None
                else:
                    print("[!] Некоторые части отработали успешно. Создаём результирующий файл из доступных данных.")
                    break

        # Объединение всех частей в один файл
        with open(result_file_path, "w", encoding="utf-8") as outfile:
            for part_result_file in result_parts:
                with open(part_result_file, "r", encoding="utf-8") as infile:
                    outfile.writelines(infile.readlines())
                os.remove(part_result_file)

        # Удаляем оригинальные части (input-файлы)
        for part in parts:
            if os.path.exists(part):
                os.remove(part)
                
        # Подсчёт строк в итоговом файле
        with open(result_file_path, "r", encoding="utf-8") as final_file:
            final_total_lines = sum(1 for _ in final_file)

        print(f"Файл с результатами: {result_file_path} сохранён и насчитывает {final_total_lines} строк.")
        return result_file_path
        
    def update_db(self, result_file):
        """Обновляет таблицу WorkSheet на основе данных из JSON-файла."""

        with open(result_file, "r", encoding="utf-8") as file:
            results = [json.loads(line) for line in file]

        for res in results:
            channel_name = res['custom_id']  # Идентификатор канала
            content = res['response']['body']['choices'][0]['message']['content']
            input_tokens = res['response']['body']['usage']['prompt_tokens']
            output_tokens = res['response']['body']['usage']['completion_tokens']

            # Ищем запись по channel_name через Django ORM
            record = WorkSheet.objects.filter(channel_name=channel_name).first()

            if record:
                # Обновляем соответствующие поля
                record.profile_channel = content
                record.profile_intokens = input_tokens
                record.profile_outtokens = output_tokens
                record.save()  # Сохраняем изменения в базе
            else:
                print(f"Запись с channel_name '{channel_name}' не найдена. Пропускаем.")

        self.stdout.write(self.style.SUCCESS("Profile данные для ТГ-каналов успешно обновлены."))