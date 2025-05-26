from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'target_audience', 'keywords', 'creatives', 'count_requested']
        labels = {
            'name': 'Название проекта',
            'description': 'Описание проекта',
            'target_audience': 'Описание ЦА',
            'keywords': 'Ключевые слова',
            'creatives': 'Примеры креативов',
            'count_requested': 'Количество каналов',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'count_requested': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'target_audience': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'keywords': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'creatives': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
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
    