from django.core.management.base import BaseCommand
from tgservice.models import Category, Channel
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import time
import re

def parse_subscribers(sub_text: str) -> int:
    """Преобразует строку вида '438.4k' в целое число 438400"""
    subs_text = subs_text.strip().lower().replace(',', '')  # На всякий случай убираем запятые
    multiplier = 1

    if 'k' in subs_text:
        multiplier = 1_000
        subs_text = subs_text.replace('k', '')
    elif 'm' in subs_text:
        multiplier = 1_000_000
        subs_text = subs_text.replace('m', '')

    try:
        return int(float(subs_text) * multiplier)
    except ValueError:
        return 0


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

class Command(BaseCommand):
    help = "Парсит категории и каналы с сайта telepot.ru и сохраняет их в базу данных"

    def handle(self, *args, **options):
        url = "https://telepot.ru/channels"
        min_subscribers = 1000

        res = requests.get(url)
        soup = BeautifulSoup(res.text, "lxml")

        for link in soup.find_all("a", href=True):
            span = link.find("span", class_="product-name strong text-secondary")
            if span:
                category_name = span.text.strip()
                full_url = urljoin(url, link["href"])

                category, _ = Category.objects.update_or_create(name=category_name, defaults={"url": full_url})
                print(f"Найдена категория: {category_name} ({full_url})")
                self.stdout.write(self.style.SUCCESS(f"Категория: {category_name} ({full_url})"))

                page = 1
                total_channels = 0

                while True:
                    page_url = f"{full_url}?page={page}"
                    print(f"Запрос страницы категории: {page_url}")

                    res_cat = requests.get(page_url)
                    print(f"Статус-код {page_url}: {res_cat.status_code}")

                    if res_cat.status_code != 200:
                        print("Ошибка: не удалось загрузить страницу категории!")
                        break
                    soup_cat = BeautifulSoup(res_cat.text, "lxml")

                    channels_on_page = []
                    new_channels = 0

                    for channel in soup_cat.find_all("a", href=True):
                        title = channel.find("span", class_="m-2 strong text-success-teal")
                        name_link_tag = channel.find("p", class_="ml-2 mt-2 mb-0 font-12 strong")

                        if title and name_link_tag:
                            full_text = name_link_tag.text.strip()
                            parts = full_text.split()

                            if len(parts) > 1:
                                name_link = " ".join(parts[:-1])
                                subscribers = parse_subscribers(parts[-1])
                            else:
                                name_link = full_text
                                subscribers = 0

                            if subscribers < min_subscribers:
                                continue

                            channel_slug = name_link.lower().replace("@", "").replace("_", "-")
                            channel_url = f"https://telepot.ru/channels/{channel_slug}"

                            time.sleep(0.5)

                            res_chan = requests.get(channel_url)
                            soup_chan = BeautifulSoup(res_chan.text, "lxml")
                            description_tag = soup_chan.find("p", itemprop="description")
                            description = description_tag.text.strip() if description_tag else ""

                            channel_obj, created = Channel.objects.update_or_create(
                                name=name_link,
                                defaults={
                                    "category": category,
                                    "title": title.text.strip(),
                                    "subscribers": subscribers,
                                    "description": description,
                                }
                            )

                            channels_on_page.append(channel_obj)
                            if created:
                                new_channels += 1
                        
                    total_channels += new_channels  # Добавляем к общему числу

                    # print(f"Страница {page}: Найдено {len(channels_on_page)} каналов → {channels_on_page}")

                    if not channels_on_page:
                        print(f"❌ Нет новых каналов на странице {page}, завершаем парсинг категории.")
                        break

                    if new_channels == 0:
                        print(f"⚠️ На странице {page} только существующие каналы, завершаем парсинг.")
                        break

                    print(f"✅ Страница {page} обработана, загружено {new_channels} каналов.")
                    page += 1

                self.stdout.write(self.style.SUCCESS(f"  → Всего каналов загружено в категории: {total_channels}"))

        self.stdout.write(self.style.SUCCESS("Завершено!"))