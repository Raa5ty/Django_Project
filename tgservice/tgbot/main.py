from tgservice.tgbot.handlers import router
from aiogram import Bot, Dispatcher
from django.conf import settings

TOKEN = settings.TG_TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Регистрируем роутер
dp.include_router(router)

# Основная функция
async def start_bot():
    try:
        print("Запуск бота...")
        await dp.start_polling(bot)  # Запускаем процесс polling для получения и обработки обновлений от Telegram
    finally:
        print("Остановка бота...")
        await bot.session.close()  # Закрываем сессию бота для корректного завершения работы и освобождения ресурсов
