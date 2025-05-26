from tgservice.tgbot.utils import TargetPipeline
from asgiref.sync import sync_to_async
from tgservice.tgbot.agents import survey_agent, result_survey_agent
from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from django.conf import settings
import logging
import os

# Настроим логирование
logging.basicConfig(level=logging.INFO)

router = Router()

# Создаём экземпляр пайплайна
pipeline = TargetPipeline(api_key=settings.OPENAI_API_KEY, index_path=settings.FAISS_INDEX_PATH)

# Состояния FSM
class Form(StatesGroup):
    in_survey = State() # Состояние для агента-анкетирования

# Финальная функция сбора данных и возврата exel файла с релевантными каналами
async def run_final_pipeline(message: Message, state: FSMContext):
    data = await state.get_data()
    dialog: str = data.get("dialog", "")

    try:
        # Запрос к RESULT агенту
        project = await result_survey_agent(dialog)

        if not project:
            await message.answer("Не удалось проанализировать диалог. Попробуй ещё раз позже.")
            await state.clear()
            return

        description_project = (
            f"Описание рекламного проекта: {project.description}\n"
            f"Описание целевой аудитории: {project.target_audience}"
            )

        # Профилирование
        profile_project = await pipeline.get_profile_creative(description_project)

        # Обновляем поле проекта в БД
        project.project_profile = profile_project
        await sync_to_async(project.save)()

        # Поиск каналов
        keywords_project = project.keywords
        top_k = project.count_requested
        relevant_objects = await pipeline.get_relevant_channels(profile_project, keywords_project, project, top_k)

        # Генерация новых креативов
        update_relevant_objects, channels_list = await pipeline.process_generate_creatives(relevant_objects, project)

        # Сохраняем в Excel
        project_id = project.id
        excel_path = await sync_to_async(pipeline.relevant_channels_to_excel)(update_relevant_objects, project_id)

        # Отправка результата
        await message.answer("Вот релевантные каналы:\n" + "\n".join(channels_list))
        await message.answer_document(FSInputFile(excel_path))
        await sync_to_async(os.remove)(excel_path)

    except Exception as e:
        print(f"[run_final_pipeline ERROR] {e}")
        await message.answer("Произошла ошибка при обработке. Попробуй позже.")

    finally:
        await state.clear()


# 1. Логика команды /help
@router.message(Command("help"))
async def help_command(message: Message):
    # Отправляем сообщение с помощью метода send_message
    await message.answer(
        "Я умею подбирать релевантные каналы под рекламную кампанию" 
        "и генерировать креативы учитывая профиль и интересы ЦА канала. Просто нажми /start"
        )
    
# 2. Логика команды /start
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await state.set_state(Form.in_survey)
    await state.update_data(dialog="")  # очищаем диалог
    await message.answer("Давай подберём ТГ-каналы и сгенерируем новые креативы под твой рекламный проект. Готов?")

@router.message(Form.in_survey)
async def handle_dialog(message: Message, state: FSMContext):
    state_data = await state.get_data()
    current_dialog = state_data.get("dialog", "")
    user_input = message.text

    # Добавляем пользовательское сообщение
    current_dialog += f"👤 Специалист: {user_input}\n"

    agent_response, new_state = await survey_agent(user_input, current_dialog)
    current_dialog += f"🤖 Агент: {agent_response}\n"

    await message.answer(agent_response)
    await state.update_data(dialog=current_dialog)

    if new_state == "in_analysis":
        await message.answer("Пожалуйста, подождите. Идёт анализ...")
        await run_final_pipeline(message, state)