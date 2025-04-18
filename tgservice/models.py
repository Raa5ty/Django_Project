from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)    
    url = models.URLField(unique=True)

    def __str__(self):
        return self.name


class Channel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="channels")
    title = models.CharField(max_length=255)
    subscribers = models.IntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="messages")
    date = models.DateTimeField()
    text = models.TextField()
    views = models.IntegerField(default=0)
    reactions = models.IntegerField(default=0)
    reposts = models.IntegerField(default=0)
    image = models.ImageField(upload_to="images/", blank=True, null=True)

    def __str__(self):
        return f"{self.channel.name} - {self.date}"

class WorkSheet(models.Model):
    channel_name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=255)
    subscribers = models.IntegerField(null=True)
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    text_messages = models.TextField(null=True)
    text_length = models.IntegerField(null=True)
    first_post_date = models.DateField(null=True)
    last_post_date = models.DateField(null=True)
    total_posts = models.IntegerField(null=True)
    active_months = models.IntegerField(null=True)
    profile_channel = models.TextField(null=True)
    profile_intokens = models.IntegerField(null=True)
    profile_outtokens = models.IntegerField(null=True)
    keywords_channel = models.TextField(null=True)
    keywords_intokens = models.IntegerField(null=True)
    keywords_outtokens = models.IntegerField(null=True)

    def __str__(self):
        return self.channel_name
    
class Project(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)  # Название Рекламной кампании
    description = models.TextField(null=True)         # Описание
    keywords = models.TextField(null=True)            # Ключевые слова (можно в виде JSON-строки или просто CSV)
    creatives = models.TextField(null=True)  # Примеры креативов
    count_requested = models.PositiveIntegerField(null=True)   # Сколько каналов запрашивали
    project_profile = models.TextField(null=True)  # Сгенерированный профиль

    def __str__(self):
        return f"{self.name} (создан: {self.created_at.strftime('%Y-%m-%d %H:%M')})"

class RelevantChannel(models.Model):
    project_name = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='results')
    channel_name = models.CharField(max_length=255, unique=True)
    category = models.CharField(max_length=255)
    subscribers = models.IntegerField(null=True)
    title = models.CharField(max_length=255, null=True)
    description = models.TextField(blank=True, null=True)
    last_post_date = models.DateTimeField(null=True)
    profile_channel = models.TextField(null=True)
    keywords_channel = models.TextField(null=True)
    score = models.FloatField(null=True)
    project_profile = models.TextField(null=True)
    new_creatives = models.TextField(null=True)

    def __str__(self):
        return f"[{self.project_name}] {self.channel_name}"

#     # Основные типы полей
#     # дата
#     # models.DateField
#     # models.DateTimeField
#     # models.TimeField
#     # # Числа
#     # models.IntegerField
#     # models.PositiveIntegerField
#     # models.PositiveSmallIntegerField
#     # models.FloatField
#     # models.DecimalField
#     # # Логический
#     # models.BooleanField
#     # # Байты (blob)
#     # models.BinaryField
#     # # Картинка
#     # models.ImageField
#     # # Файл
#     # models.FileField
#     # # url, email
#     # models.URLField
#     # models.EmailField

#     def __str__(self):
#         return self.name