from django.core.management.base import BaseCommand
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from django.conf import settings
import os


class Command(BaseCommand):
    help = "Проверяет параметры сохранённой FAISS индексной базы"

    def add_arguments(self, parser):
        parser.add_argument(
            '--index-name',
            type=str,
            required=True,
            help="Имя папки с индексом внутри tgservice (например: Index_DB_12-05-2025)"
        )

    def handle(self, *args, **options):
        index_name = options['index_name']
        index_path = os.path.join(settings.BASE_DIR, 'tgservice', index_name)

        if not os.path.exists(index_path):
            self.stdout.write(self.style.ERROR(f"Папка {index_name} не найдена по пути {index_path}"))
            return

        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
            vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

            num_docs = len(vectorstore.docstore._dict)
            embedding_dim = vectorstore.index.d

            self.stdout.write(self.style.SUCCESS(f"Индекс загружен из: {index_path}"))
            self.stdout.write(self.style.SUCCESS(f"Количество документов: {num_docs}"))
            self.stdout.write(self.style.SUCCESS(f"Размерность эмбеддингов: {embedding_dim}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при загрузке индекса: {str(e)}"))