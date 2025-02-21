from django.db import models

# Create your models here.
# class Category(models.Model):
#     # Id не надо, он уже сам появиться
#     name = models.CharField(max_length=16, unique=True)
#     description = models.TextField(blank=True)

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