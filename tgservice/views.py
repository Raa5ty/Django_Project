from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from tgservice.forms import ProjectForm
from tgservice.models import Project, RelevantChannel, WorkSheet, Category
from tgservice.tgbot.utils import TargetPipeline
from tgservice.utils import generate_excel_for_project 
from asgiref.sync import async_to_sync
from django.conf import settings
from datetime import datetime

# Создаём один экземпляр для всего модуля
pipeline = TargetPipeline(
    api_key=settings.OPENAI_API_KEY,
    index_path=settings.FAISS_INDEX_PATH
)

# Create your views here.

class MainView(LoginRequiredMixin, TemplateView):
    template_name = "tgservice/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Добро пожаловать в TG-Service"
        return context

# Сохранение результатов подбора в excel
@login_required(login_url='/')
def download_excel(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    excel_file = generate_excel_for_project(project)

    if not excel_file:
        return Http404("Нет данных для выгрузки.", status=404)

    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=project_{project_id}_results.xlsx'
    return response

# Страница формы Проекта и вывода результата с защитой
@login_required(login_url='/')
def search_view(request):
    form = ProjectForm()
    project = None
    channels = []

    project_id = request.GET.get("project_id")
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        form = ProjectForm(instance=project)
        channels = RelevantChannel.objects.filter(project=project)
        
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()

            description_project = (
                f"Описание рекламного проекта: {project.description}\n"
                f"Описание целевой аудитории: {project.target_audience}"
            )

            # Получаем профиль проекта (асинхронные вызовы через обёртку)
            profile = async_to_sync(pipeline.get_profile_creative)(description_project)
            project.project_profile = profile
            project.save()

            # Получаем релевантные каналы
            relevant_objects = async_to_sync(pipeline.get_relevant_channels)(
                profile_project=profile,
                keywords_project=project.keywords,
                project=project,
                top_k=project.count_requested
            )

            # Генерируем креативы
            update_relevant_objects, _ = async_to_sync(pipeline.process_generate_creatives)(relevant_objects, project)

            channels = update_relevant_objects

            # После POST — редирект на GET, чтобы избежать повторной отправки
            return redirect(f"{request.path}?project_id={project.id}")

    return render(request, "tgservice/search.html", {
        "form": form,
        "project": project,
        "channels": channels,
    })

# Страница Проектов
class ProjectsView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "tgservice/projects.html"
    context_object_name = "projects"
    ordering = ["-created_at"]

# Страница Всех каналов в БД    
class ChannelsView(LoginRequiredMixin, ListView):
    model = WorkSheet
    template_name = "tgservice/channels.html"
    context_object_name = "channels"
    paginate_by = 100
    ordering = ["-subscribers"]  # или last_post_date

    def get_queryset(self):
        queryset = super().get_queryset()

        # фильтр по категории
        categories = self.request.GET.getlist("category")
        if categories:
            queryset = queryset.filter(category__in=categories)

        # фильтр по минимальному количеству подписчиков
        min_subs = self.request.GET.get("min_subs")
        if min_subs:
            queryset = queryset.filter(subscribers__gte=int(min_subs))

        # фильтр по максимальному количеству подписчиков
        max_subs = self.request.GET.get("max_subs")
        if max_subs:
            queryset = queryset.filter(subscribers__lte=int(max_subs))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Каналы из базы данных"
        context['all_categories'] = Category.objects.all()
        context['selected_categories'] = self.request.GET.getlist("category")
        context['min_subs'] = self.request.GET.get("min_subs", "")
        context['max_subs'] = self.request.GET.get("max_subs", "")
        return context

# Пустой шаблон с защитой
@login_required(login_url='/')
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