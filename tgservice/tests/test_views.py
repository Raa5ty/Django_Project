from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.http import Http404, HttpResponseNotFound
from io import BytesIO
from openpyxl import Workbook
from django.urls import reverse
from unittest.mock import patch
from tgservice.models import WorkSheet, Project, RelevantChannel
from mixer.backend.django import mixer

class MainViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('tgservice:main'))  
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_main_view_logged_in(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('tgservice:main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tgservice/main.html')
        self.assertContains(response, "Добро пожаловать в TG-Service")

class SearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.url = reverse('tgservice:search') 

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_get_view_logged_in_without_project_id(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")  

    def test_get_view_with_project_id(self):
        self.client.login(username='testuser', password='testpass')
        project = Project.objects.create(name='Test Project')
        response = self.client.get(self.url + f"?project_id={project.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Project")

    @patch("tgservice.views.pipeline.get_profile_creative")
    @patch("tgservice.views.pipeline.get_relevant_channels")
    @patch("tgservice.views.pipeline.process_generate_creatives")
    def test_post_creates_project_and_redirects(self, mock_creatives, mock_relevant, mock_profile):
        self.client.login(username='testuser', password='testpass')

        mock_profile.return_value = "test_profile"
        mock_relevant.return_value = []
        mock_creatives.return_value = ([], None)

        data = {
            'name': 'Test Project',
            'description': 'Test Description',
            'target_audience': 'Test Audience',
            'keywords': 'keyword1, keyword2',
            'count_requested': 5,
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(name='Test Project').exists())

        project = Project.objects.get(name='Test Project')
        self.assertEqual(project.project_profile, "test_profile")
        self.assertIn(f"?project_id={project.id}", response.url)

class ProjectsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.url = reverse('tgservice:projects')  

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_view_projects_list(self):
        self.client.login(username='testuser', password='12345')
        mixer.cycle(3).blend(Project)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tgservice/projects.html")
        self.assertIn("projects", response.context)
        self.assertEqual(len(response.context["projects"]), 3)

class ChannelsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.url = reverse('tgservice:channels')  

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_view_channels_list(self):
        self.client.login(username='testuser', password='12345')
        mixer.cycle(5).blend(WorkSheet, subscribers=1000, category='Marketing')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tgservice/channels.html")
        # Проверяем пагинированный вывод
        page_obj = response.context["page_obj"]  # <- Используем page_obj
        self.assertEqual(page_obj.paginator.count, 5)  

    def test_filter_by_category(self):
        self.client.login(username='testuser', password='12345')
        mixer.blend(WorkSheet, category='Marketing')
        mixer.blend(WorkSheet, category='Finance')
        response = self.client.get(f"{self.url}?category=Marketing")

        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]  # <- Используем page_obj
        self.assertEqual(page_obj.paginator.count, 1)  
        self.assertEqual(response.context["selected_categories"], ['Marketing'])

    def test_filter_by_subscribers_range(self):
        self.client.login(username='testuser', password='12345')
        mixer.blend(WorkSheet, subscribers=1000)
        mixer.blend(WorkSheet, subscribers=5000)
        mixer.blend(WorkSheet, subscribers=10000)
        response = self.client.get(f"{self.url}?min_subs=2000&max_subs=8000")

        page_obj = response.context["page_obj"]  # <- Используем page_obj
        self.assertEqual(page_obj.paginator.count, 1)  

class DownloadExcelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.project = mixer.blend(Project)  # Создаём тестовый проект
        self.url = reverse('tgservice:download_excel', args=[self.project.id])

    def test_login_required(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/login/?next={self.url}")

    @patch('tgservice.views.generate_excel_for_project')
    def test_download_excel_success(self, mock_generate):
        mock_excel_file = BytesIO()
        workbook = Workbook()
        workbook.save(mock_excel_file)
        mock_excel_file.seek(0)
        mock_generate.return_value = mock_excel_file

        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Disposition'],
            f'attachment; filename=project_{self.project.id}_results.xlsx'
        )
        self.assertEqual(
            response['Content-Type'], 
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    @patch('tgservice.views.generate_excel_for_project')
    def test_download_excel_empty_data(self, mock_generate):
        mock_generate.return_value = None # Функция возвращает None (нет данных)

        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)

        # Проверяем, что возвращается HttpResponseNotFound (404)
        self.assertEqual(response.status_code, 404)
        self.assertIsInstance(response, HttpResponseNotFound)

