from openai import AsyncOpenAI
from tgservice.models import Project
from tgservice.tgbot.prompts import (
    SURVEY_SYSTEM_PROMPT,
    SURVEY_USER_PROMPT,
    RESULT_SURVEY_SYSTEM_PROMPT,
    RESULT_SURVEY_USER_PROMPT,
)
from asgiref.sync import sync_to_async
import json

# Инициализация клиента OpenAI — ты должен сам передать API-ключ как переменную окружения или иным способом
client = AsyncOpenAI()

# Функция Async: SURVEY-agent
async def survey_agent(user_message: str, current_dialogue: str):
    system_prompt = SURVEY_SYSTEM_PROMPT

    user_prompt = SURVEY_USER_PROMPT.format(
        current_dialogue=current_dialogue or "",
        user_message=user_message
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        result = completion.choices[0].message.content
        data = json.loads(result)

        if isinstance(data, dict) and {"agent_answer", "state"}.issubset(data.keys()):
            return data["agent_answer"], data["state"]
        else:
            raise ValueError("Неверная структура ответа GPT")

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Ошибка при анализе ответа SURVEY-agent: {e}")
        return None, None

# Функция Async: RESULT-agent
async def result_survey_agent(current_dialogue: str):
    system_prompt = RESULT_SURVEY_SYSTEM_PROMPT

    user_prompt = RESULT_SURVEY_USER_PROMPT.format(
        current_dialogue=current_dialogue or ""
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        result = completion.choices[0].message.content
        data = json.loads(result)

        # Проверка верхнего уровня
        expected_keys = {"name", "description", "target_audience", "keywords", "creatives", "count_requested"}
        if not isinstance(data, dict) or not expected_keys.issubset(data.keys()):
            raise ValueError("Неверная структура ответа GPT")
        
        # Проверяем словарь на лишние ключи перед сохранением в базу данных
        allowed_fields = {"name", "description", "target_audience", "keywords", "creatives", "count_requested"}
        filtered_data = {key: data[key] for key in allowed_fields if key in data}

        project = await sync_to_async(Project.objects.create)(**filtered_data)

        return project # возвращаем сам объект проекта

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Ошибка при анализе ответа RESULT-agent: {e}")
        return None