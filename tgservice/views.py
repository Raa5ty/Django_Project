from django.shortcuts import render, redirect
from .forms import ProjectForm

# Create your views here.
def main_view(request):
    form = ProjectForm()
    return render(request, "tgservice/index.html", context={'form': form})

def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)  # Получаем данные из формы
        if form.is_valid():  # Проверяем валидность формы
            form.save()  # Сохраняем данные в базе
            return redirect('project_list')  # Перенаправляем на список проектов
    else:
        form = ProjectForm()  # Пустая форма для GET-запроса

    return render(request, 'create_project.html', {'form': form})  # Отображаем форму в шаблоне