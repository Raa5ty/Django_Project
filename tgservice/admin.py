from django.contrib import admin
from django.db.models import Count
from .models import Category, Channel, Message

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_filter = ["name"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by("name")  # Сортировка по алфавиту

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    search_fields = ["name", "title"]  # Поиск по имени и заголовку
    list_filter = ["category"]  # Фильтр по категории
    list_display = ["name", "category", "message_count"]  # Отображаем количество сообщений
     
    def get_queryset(self, request):
        queryset = super().get_queryset(request) # Получаем стандартный QuerySet
        return queryset.annotate(msg_count=Count("messages")) # Добавляем аннотацию с подсчётом сообщений

    def message_count(self, obj):
        return obj.msg_count
    message_count.admin_order_field = "msg_count"  # Позволяет сортировать по количеству сообщений
    message_count.short_description = "Count messages"  # Заголовок столбца в админке

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    search_fields = ["text"]  # Поиск по тексту сообщений
    list_filter = [("channel", admin.RelatedOnlyFieldListFilter)]  # Обычный фильтр по каналам, без кнопки счётчика
    date_hierarchy = "date"  # Добавляет фильтр по дате