from django.db import models

# Create your models here.
class Category(models.Model):
    # Id не надо, он уже сам появиться     
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

    
class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    profile = models.TextField()
    keywords = models.TextField()
    creative = models.TextField()
    num_channels = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)  # Дата и время создания

    def __str__(self):
        return self.name

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