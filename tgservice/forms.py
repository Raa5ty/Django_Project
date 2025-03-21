from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'profile', 'keywords', 'creative', 'num_channels']  # Не включаем created_at
        labels = {
            'name': 'Название проекта',
            'description': 'Описание проекта',
            'profile': 'Профиль ЦА',
            'keywords': 'Ключевые слова',
            'creative': 'Пример креатива',
            'num_channels': 'Количество каналов',
        }

# Форма для поиска релевантныхх каналов под рекламную кампанию
# class ProjectForm(forms.Form):
#     # Поля формы
#     name = forms.CharField(label='Название проекта', max_length=100)
#     description = forms.CharField(label='Описание проекта')
#     profile = forms.CharField(label='Профиль ЦА')
#     keywords = forms.CharField(label='Ключевые слова')
#     creative = forms.CharField(label='Пример креатива')
#     num_channels = forms.IntegerField(label='Количество каналов')
    