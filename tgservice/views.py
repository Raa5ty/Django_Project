from django.shortcuts import render, redirect
from .forms import ProjectForm

# Create your views here.
def main_view(request):
    return render(request, "tgservice/index.html", context={})

def search_view(request):
    form = ProjectForm()
    return render(request, "tgservice/search.html", context={'form': form})

def projects_view(request):
    return render(request, "tgservice/projects.html")
    
def database_view(request):
    return render(request, "tgservice/database.html")

def empty_view(request):
    return render(request, "tgservice/empty.html")

# def create_project(request):
#     if request.method == 'POST':
#         form = ProjectForm(request.POST)  # Получаем данные из формы
#         if form.is_valid():  # Проверяем валидность формы
#             form.save()  # Сохраняем данные в базе
#             return redirect('project_list')  # Перенаправляем на список проектов
#     else:
#         form = ProjectForm()  # Пустая форма для GET-запроса

#     return render(request, 'create_project.html', {'form': form})  # Отображаем форму в шаблоне