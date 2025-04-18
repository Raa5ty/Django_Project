from django.core.management.base import BaseCommand
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from tgservice.models import WorkSheet
from django.conf import settings
import time
import os


class Command(BaseCommand):
    help = 'Создаёт индексную базу FAISS из профилей каналов'

    def handle(self, *args, **options):
        self.create_indexdb()

    def create_indexdb(self, embedding_model="text-embedding-ada-002"):
        """Создаёт индексную базу FAISS и сохраняет её."""
        indexdb_filename = f"Index_DB_{time.strftime('%d-%m-%Y')}"
        index_path = os.path.join(settings.BASE_DIR, 'tgservice', indexdb_filename)

        result = WorkSheet.objects.values_list(
            "channel_name", "profile_channel", "keywords_channel"
        )

        documents = []

        for channel_name, profile_channel, keywords_channel in result:
            page_content = f"Профиль целевой аудитории канала:\n{profile_channel}\nКлючевые слова канала: {keywords_channel}"
            metadata = {"channel_name": channel_name}
            documents.append(Document(page_content=page_content, metadata=metadata))

        embeddings = OpenAIEmbeddings(model=embedding_model)
        vectorstore = FAISS.from_documents(documents, embeddings)

        vectorstore.save_local(index_path)
        self.stdout.write(self.style.SUCCESS(f"Индекс сохранён в : tgservice/{indexdb_filename}"))