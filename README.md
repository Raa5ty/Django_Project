Приложение Tgservice, описание БД в модуле tgservice/models с классами Category, Channel, Message для ТГ-каналов.
Для парсинга данных написаны админ-команды Django для заполнения БД, на основе библиотек BeautifulSoup и API Telethon (tgservice\management\commands\fill_db.py, tgservice\management\commands\fill_posts.py).
Произведены все необходимые настройки приложения в tgservice/models, tgservice/admin и settings для работы парсеров и взаимодействия с БД через админку django проекта.

В последствии из текстовых данных канала моделью (OpenAI) будет возвращаться профиль ЦА и список ключевых слов, для этого будет создана ещё одна таблица в БД (класс).
