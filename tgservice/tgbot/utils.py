from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from tgservice.models import WorkSheet
from tgservice.prompts import system_creative, system_new_creative
from django.conf import settings
import pandas as pd
import os

api_key=settings.OPENAI_API_KEY

# Загрузка индексной базы данных
def load_faiss_index(index_path: str):
    return FAISS.load_local(index_path, OpenAIEmbeddings(), allow_dangerous_deserialization=True)

class OpenAIRequests:
    def __init__(self, api_key):
        self.client = AsyncOpenAI(api_key=api_key)

    # Функция получения профиля ЦА для рекламного креатива
    async def get_profile_creative(self, content, system=system_creative, model='gpt-4o-mini', temp=0.3):  
        messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f'''
                        Проведи анализ рекламной кампании и креатива, и сформулируй ответ, описывающий портрет целевой аудитории на которую нацелена данная кампания.
                        Ответ дай строго по шаблону.
                        Шаблон ответа:
                        "Социальный портрет: мужчины, возраст 18-25, холостые, работники по найму/специалисты, уровень дохода средний (80 000–200 000 рублей)\n
                        Интересы: спорт, финансы, способы увеличения дохода, инвестирование, путешествия\n
                        Потребности: финансовая стабильность и безопасность, карьера, саморазвитие, здоровье, развлечения\n"
                        Описание ракламной кампании и пример креатива: {content}
                        '''}
        ]

        completion = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp
        )

        return completion.choices[0].message.content
    
    # Функция для создания нового креатива на основе профиля ЦА и рекламной кампании
    async def get_new_creatives(self, message_text, channels_profile, description_campaign, creatives, system=system_new_creative, model='gpt-4o-mini', temp=0.4):
        messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f''' 
                        Описание рекламной кампании: {description_campaign}.  
                        Примеры креатива(-ов) (если есть): {creatives}.
                        Контент Telegram-канала: {message_text}. 
                        Профиль целевой аудитории: {channels_profile}.
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
                        "Креатив 1";\n"Креатив 2";\n"Креатив 3".
                        
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

# Создадим функцию для подбора релевентных каналов по креативам, на вход подаём датафрейм с креативами и индексную базу данных
def get_relevant_channels(index, description_campaign, creatives_profile, creatives_keywords, top_k=10):
    # Логика получения релевантных каналов
    results = []
    search_query = f"{creatives_profile}\nКлючевые слова: {creatives_keywords}"
    relevant_channels = index.similarity_search_with_score(search_query, k=top_k, nprobe=10)

    
    for channel, score in relevant_channels:    
        channel_name_meta = channel.metadata['channel_name']
        result = WorkSheet.objects.filter(channel_name=channel_name_meta).first()
            
        # Если данные есть, извлекаем их, иначе присваиваем None только отсутствующим значениям
        if result:
            channel_name = result.channel_name
            category = result.category
            subscribers = result.subscribers
            title = result.title
            description = result.description
            last_post_date = result.last_post_date
            profile_channel = result.profile_channel
            keywords_channel = result.keywords_channel
        else:
            channel_name = channel_name_meta
            category = None
            subscribers = None
            title = None
            description = None
            last_post_date = None
            profile_channel = None
            keywords_channel = None

        # Добавляем результат в список
        results.append({
                'channel_name': channel_name,
                'category': category,
                'subscribers': subscribers,
                'title': title,
                'description_ch': description,
                'last_post_date': last_post_date,
                'channels_profile': profile_channel,
                'channels_keywords': keywords_channel,
                'score': score,
                'description_campaign': description_campaign,
                'creatives_profile': creatives_profile,
                'creatives_keywords': creatives_keywords
            })

    # Создаем DataFrame из результатов и сохраняем в csv файл
    relevant_channels_df = pd.DataFrame(results)
    return relevant_channels_df

create = OpenAIRequests(api_key)

# Функция обработки ответа от LLM по генерации нового креатива и сохранения всех данных в дф
async def process_generate_creatives(relevant_channels_df, creatives): 
    new_creatives = []
    channels = []

    # Создаем цикл по relevant_channels_df и вытаскиваем следующие данные
    for _, row in relevant_channels_df.iterrows():
        descriptions_rc = row['description_campaign']
        channel_name = row['channel_name']
        profile_ch = row['channels_profile']

        # Получаем message_text из базы данных session.query(WorkSheet.text_messages).filter(WorkSheet.channel_name == channel_name).first()
        result = WorkSheet.objects.filter(channel_name=channel_name).only("text_messages").first()
        message_text = result.text_messages if result else None

        # Получаем новый креатив через функцию
        new_creative = await create.get_new_creatives(
            message_text=message_text,
            channels_profile=profile_ch,
            description_campaign=descriptions_rc,
            creatives=creatives
        )
        # Добавляем полученные значения в список
        new_creatives.append(new_creative)
        channels.append(channel_name)

    # Добавляем 'new_creatives' в конец DataFrame
    relevant_channels_df['new_creatives'] = new_creatives

    # Сохраняем обновлённый DataFrame в файл
    return relevant_channels_df, channels