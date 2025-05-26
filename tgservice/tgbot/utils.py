from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from asgiref.sync import sync_to_async
from tgservice.models import WorkSheet, RelevantChannel
from tgservice.prompts import system_profile_project, system_new_creative
from django.conf import settings
import pandas as pd
import time
import os


class TargetPipeline:
    def __init__(self, api_key, index_path):
        self.client = AsyncOpenAI(api_key=api_key)
        self.index = FAISS.load_local(index_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True)

    # Функция получения профиля ЦА для рекламного креатива
    async def get_profile_creative(self, description_project, system=system_profile_project, model='gpt-4o-mini', temp=0.3):  
        messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f'''
                        Проведи анализ рекламной кампании и целевой аудитории, и сформулируй профиль целевой аудитории на которую нацелена данная кампания.
                        Ответ дай строго по шаблону.
                        Шаблон ответа:
                        "Социальный портрет: мужчины, возраст 18-25, холостые, работники по найму/специалисты, уровень дохода средний (80 000–200 000 рублей)\n
                        Интересы: спорт, финансы, способы увеличения дохода, инвестирование, путешествия\n
                        Потребности: финансовая стабильность и безопасность, карьера, саморазвитие, здоровье, развлечения\n"
                        Описание рекламной кампании и целевой аудитории:\n
                        {description_project}
                        '''}
        ]

        completion = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp
        )

        return completion.choices[0].message.content
    
    # Функция для создания нового креатива на основе профиля ЦА и рекламной кампании
    async def get_new_creatives(self, message_text, profile_channel, description_project, creatives, system=system_new_creative, model='gpt-4o-mini', temp=0.4):
        messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f''' 
                        Описание рекламной кампании: {description_project}.  
                        Примеры креатива(-ов) (если есть): {creatives}.
                        Контент Telegram-канала: {message_text}. 
                        Профиль целевой аудитории: {profile_channel}.
                        Твоя задача:
                            1. Проведи анализ предоставленных данных, чтобы понять ключевые цели и задачи рекламной кампании.
                            2. Изучи пример(-ы) креатива, чтобы учесть стиль, тональность и идеи.
                            3. Учитывай тематику, стилистику и ценности контента Telegram-канала.
                            4. Учитывай интересы, потребности и страхи целевой аудитории.
                            5. Создай креатив, соответствующий следующим критериям:
                                - Ясный, ёмкий текст длиной до 160 символов.
                                - Чёткий и мотивирующий призыв к действию (CTA).
                                - Соответствие техническим рекомендациям Telegram Ads (ограничения на формат текста и использование эмодзи до 10 штук).
                                - Уникальность, но соответствие предоставленным данным.
                            
                        В ответ предоставь до трёх креативов в формате:
                        "'Креатив_1';\n'Креатив_2';\n'Креатив_3';"
                        
                        Никаких дополнительных комментариев, только тексты креативов.
                        '''
                        }
        ]

        completion = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp
        )

        return completion.choices[0].message.content

    #Функция для подбора релевентных каналов по креативам, на вход подаём индексную БД, профиль проекта, ключи проекта, количество искомых каналов
    async def get_relevant_channels(self, profile_project, keywords_project, project, top_k=10):
        search_query = f"{profile_project}\nКлючевые слова: {keywords_project}"
        relevant_channels = self.index.similarity_search_with_score(search_query, k=top_k, nprobe=10)

        relevant_objects = [] 

        for channel, score in relevant_channels:    
            channel_name_meta = channel.metadata['channel_name']
            result = await sync_to_async(lambda: WorkSheet.objects.filter(channel_name=channel_name_meta).first())()
                
            # Собираем данные
            data = {
                "project": project,
                "channel_name": channel_name_meta,
                "category": result.category if result else None,
                "subscribers": result.subscribers if result else None,
                "title": result.title if result else None,
                "description": result.description if result else None,
                "last_post_date": result.last_post_date if result else None,
                "profile_channel": result.profile_channel if result else None,
                "keywords_channel": result.keywords_channel if result else None,
                "score": score,
                "new_creatives": None
            }

            # Создаём и сохраняем объект RelevantChannel
            obj = await sync_to_async(RelevantChannel.objects.create)(**data)
            relevant_objects.append(obj)

        return relevant_objects # возвращаем список объектов RelevantChannel

    # Функция генерации нового креатива и сохранения всех данных в RelevantChannel
    async def process_generate_creatives(self, relevant_objects, project): 
        new_relevant_objects = []
        channels = []

        # Создаем цикл по relevant_channels_df и вытаскиваем следующие данные
        for ch in relevant_objects:
            channel_name = ch.channel_name
            profile_ch = ch.profile_channel

            # Получаем message_text из базы данных session.query(WorkSheet.text_messages).filter(WorkSheet.channel_name == channel_name).first()
            result = await sync_to_async(lambda: WorkSheet.objects.filter(channel_name=channel_name).only("text_messages").first())()
            message_text = result.text_messages if result else ""

            # Получаем новый креатив через функцию
            new_creative = await self.get_new_creatives(
                message_text=message_text,
                profile_channel=profile_ch,
                description_project=project.description,
                creatives=project.creatives
            )
            
            # Добавляем новый креатив в модель релевантных каналов
            ch.new_creatives = new_creative
            await sync_to_async(ch.save)()

            # Добавляем полученные значения в список
            new_relevant_objects.append(ch)
            channels.append(channel_name)

        # Сохраняем обновлённый DataFrame в файл
        return new_relevant_objects, channels

    # Создаём итоговый excel файл
    def relevant_channels_to_excel(self, objects_list, project_id, filename_prefix="result_file"):
        # Абсолютный путь до папки, где будут храниться файлы
        filename = f"{filename_prefix}_{project_id}_{int(time.time())}.xlsx"
        file_path = os.path.join(settings.BASE_DIR, "tgservice", "excel_files", filename)

        # Выбираем нужные поля из объектов
        data = [
            {
                "channel_name": obj.channel_name,
                "category": obj.category,
                "subscribers": obj.subscribers,
                "title": obj.title,
                "description": obj.description,
                "last_post_date": obj.last_post_date,
                "profile_channel": obj.profile_channel,
                "keywords_channel": obj.keywords_channel,
                "score": obj.score,
                "new_creatives": obj.new_creatives,
            }
            for obj in objects_list
        ]

        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False, engine="openpyxl")
        return file_path
