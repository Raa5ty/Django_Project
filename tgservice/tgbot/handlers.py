from tgservice.tgbot.utils import OpenAIRequests, get_relevant_channels, process_generate_creatives, load_faiss_index
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from django.conf import settings
import logging
import pandas as pd

# Настроим логирование
logging.basicConfig(level=logging.INFO)

router = Router()

# Загрузка баз данных
index = load_faiss_index('Index_FAIS_DB')

api_key = settings.OPENAI_API_KEY

profile = OpenAIRequests(api_key)

# Состояния FSM
class Form(StatesGroup):
    describing_campaign = State() # Состояние для описания рекламной кампании
    uploading_creatives = State() # Состояние для загрузки креативов
    inputting_keywords = State() # Состояние для ввода ключевых слов
    profile_creative = State() # Состояние для получения профиля ЦА
    selecting_top_k  = State() # Состояние для выбора количества релевантных каналов

# 1. Логика команды /help
@router.message(Command("help"))
async def help_command(message: types.Message):
    # Отправляем сообщение с помощью метода send_message
    await message.answer("Я могу помочь вам подобрать релевантные каналы под рекламную кампанию и сгенерировать креативы учитывая профиль и интересы ЦА канала.")
    
# 2. Логика команды /start
@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await message.answer("""Для начала опишите кратко рекламную кампанию, с каким каналом или ресурсом она связана и на кого нацелена.""")
    await state.set_state(Form.describing_campaign)

# Обработка ответа на описание кампании
@router.message(Form.describing_campaign)
async def describe_campaign(message: types.Message, state: FSMContext):
    campaign_description = message.text
    await state.update_data(campaign_description=campaign_description)

    # Запрашиваем креативы
    await message.answer("Отправьте примеры рекламных креативов, которые вы хотели бы использовать в этой кампании.\nЕсли креативов несколько, возьмите каждый в кавычки и разделите точкой с запятой")
    await state.set_state(Form.uploading_creatives)

# Обработка ответа на креативы
@router.message(Form.uploading_creatives)
async def upload_creatives(message: types.Message, state: FSMContext):
    creatives = message.text
    await state.update_data(creatives=creatives)
    user_data = await state.get_data()

    # Объединяем данные (описание кампании и креативы)
    combined_data = user_data['campaign_description'] + " " + creatives

    try:
        # Отправляем объединенные данные в функцию
        response = await profile.get_profile_creative(combined_data)
        
        # Проверяем корректность ответа
        if not response or not isinstance(response, str):
            await message.answer("Произошла ошибка при создании профиля креатива. Попробуйте снова.")
            return

        # Сохраняем ответ
        await state.update_data(profile_creative=response)

    except Exception as e:
        # Логируем ошибку
        print(f"Ошибка при обработке профиля креатива: {e}")
        
        # Сообщение пользователю
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")

    # Переход к следующему этапу
    await message.answer("Напишите от 10 до 20 ключевых слов или фраз через запятую, описывающих вашу рекламную кампанию.")
    await state.set_state(Form.inputting_keywords)

# Обработка ввода ключевых слов
@router.message(Form.inputting_keywords)
async def input_keywords(message: types.Message, state: FSMContext):
    keywords_profile = message.text
    await state.update_data(keywords_profile=keywords_profile) 

    # Запрашиваем какое количество релевантных каналов необходимо получить
    await message.answer("Какое количество релевантных каналов вы хотите получить? Отправте числом.\nУчтите, что каналы по релевантности в csv файле сформируются вниз по убывающей.")
    await state.set_state(Form.selecting_top_k)

# Обработка ввода количества каналов
@router.message(Form.selecting_top_k)
async def select_top_k(message: types.Message, state: FSMContext):
    try:
        # Получаем значение от пользователя
        top_k = int(message.text)

        # Извлекаем сохранённые данные
        user_data = await state.get_data()
        description_campaign = user_data['campaign_description']
        created_profile = user_data['profile_creative'] 
        keywords_profile = user_data['keywords_profile']

        # Отправляем объединенные данные в функцию get_relevant_channels
        relevant_channels_df = get_relevant_channels(index, description_campaign, created_profile, keywords_profile, top_k=top_k)

        await message.answer(f"Релевантные каналы подобраны. Генерируются новые креативы...")

        # Извлечение креативов из состояния
        creatives = user_data['creatives']

        # Следующим запросов из созданной дф получаем к каждому найденому каналу сгенерированный креатив
        relevant_channels_with_created_creative_df, channels_list = await process_generate_creatives(relevant_channels_df, creatives)

        #Сохраняем результаты в CSV файл
        relevant_channels_with_created_creative_df.to_excel('result_file.xlsx', index=False, engine='openpyxl')

        # Отправляем файл пользователю
        await message.answer("Найденные каналы:\n" + "\n".join((channels_list)))
        await message.answer_document(types.FSInputFile('result_file.xlsx'))

    except ValueError:
        # Обработка некорректного ввода
        await message.answer("Пожалуйста, введите число.")
