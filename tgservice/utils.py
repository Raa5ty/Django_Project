import io
import pandas as pd
from .models import RelevantChannel

def generate_excel_for_project(project):
    channels = RelevantChannel.objects.filter(project=project)
    if not channels.exists():
        return None

    data = []
    for ch in channels:
        data.append({
            "Название канала": ch.channel_name,
            "Категория": ch.category,
            "Подписчики": ch.subscribers,
            "Заголовок": ch.title,
            "Описание": ch.description,
            "Дата последнего поста": ch.last_post_date,
            "Профиль канала": ch.profile_channel,
            "Ключевые слова": ch.keywords_channel,
            "Оценка": ch.score,
            "Креативы": ch.new_creatives,
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Релевантные каналы')

    output.seek(0)
    return output
