from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'project_profile', 'keywords', 'creatives', 'count_requested']
        labels = {
            'name': 'Название проекта',
            'description': 'Описание проекта',
            'project_profile': 'Профиль ЦА',
            'keywords': 'Ключевые слова',
            'creatives': 'Примеры креативов',
            'count_requested': 'Количество каналов',
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
    