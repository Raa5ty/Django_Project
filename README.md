Приложение Tgservice, описание БД в модуле tgservice/models с классами Category, Channel, Message для ТГ-каналов.
Для парсинга данных написаны админ-команды Django для заполнения БД, на основе библиотек BeautifulSoup и API Telethon (tgservice\management\commands\fill_db.py, tgservice\management\commands\fill_posts.py).
Произведены все необходимые настройки приложения в tgservice/models, tgservice/admin и settings для работы парсеров и взаимодействия с БД через админку django проекта.

В последствии из текстовых данных канала и промта моделью (OpenAI) будет возвращаться профиль ЦА а так же список ключевых слов, для этих данных будет создана ещё одна таблица в БД (класс).

В итоге из профелей (ЦА) и ключей канала мы создадим индексную базу данных FAISS.
