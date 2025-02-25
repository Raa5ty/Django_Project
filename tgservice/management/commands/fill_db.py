from django.core.management.base import BaseCommand
from tgservice.models import Category, Channel
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import time
import re

def parse_subscribers(sub_text: str) -> int:
    """Парсит строку с числом подписчиков в int"""
    match = re.match(r"([\d.]+)([KkMm])?", sub_text)
    if not match:
        return 0

    num, suffix = match.groups()
    num = float(num.replace(".", ""))

    if suffix in ["K", "k"]:
        return int(num * 1_000)
    elif suffix in ["M", "m"]:
        return int(num * 1_000_000)
    return int(num)


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

class Command(BaseCommand):
    help = "Парсит категории и каналы с сайта telepot.ru и сохраняет их в базу данных"

    def handle(self, *args, **options):
        url = "https://telepot.ru/channels"
        min_subscribers = 1000

        res = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(res.text, "lxml")

        for link in soup.find_all("a", href=True):
            span = link.find("span", class_="product-name strong text-secondary")
            if span:
                category_name = span.text.strip()
                full_url = urljoin(url, link["href"])

                category, created = Category.objects.get_or_create(name=category_name, defaults={"url": full_url})

                self.stdout.write(self.style.SUCCESS(f"Категория: {category_name}"))

                page = 1

                while True:
                    page_url = f"{full_url}?page={page}"
                    res_cat = requests.get(page_url, headers=headers)
                    soup_cat = BeautifulSoup(res_cat.text, "lxml")

                    channels_on_page = []

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

                            time.sleep(1)

                            res_chan = requests.get(channel_url, headers=headers)
                            soup_chan = BeautifulSoup(res_chan.text, "lxml")
                            description_tag = soup_chan.find("p", itemprop="description")
                            description = description_tag.text.strip() if description_tag else ""

                            channel_obj, created = Channel.objects.get_or_create(
                                name=name_link,
                                defaults={
                                    "category": category,
                                    "title": title.text.strip(),
                                    "subscribers": subscribers,
                                    "description": description,
                                }
                            )

                            channels_on_page.append(channel_obj)

                    if not channels_on_page:
                        break

                    page += 1

                self.stdout.write(self.style.SUCCESS(f"  → Каналов загружено: {len(channels_on_page)}"))

        self.stdout.write(self.style.SUCCESS("Завершено!"))