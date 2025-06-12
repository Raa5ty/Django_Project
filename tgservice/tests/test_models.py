from django.test import TestCase
from tgservice.models import Category, Channel, Message, WorkSheet, Project, RelevantChannel
# FactoryBoy - используется если нужен полный контроль над тестами, сперва создаются фабрики под каждую модель с типами данных и пр.
# mixer - полностью создаёт fake модели самостоятельно
from mixer.backend.django import mixer

# Create your tests here.
class CategoryModelTest(TestCase):
    def test_str_method(self):
        category = mixer.blend(Category)
        self.assertEqual(str(category), category.name)

class ChannelModelTest(TestCase):
    def test_str_method(self):
        channel = mixer.blend(Channel)  # Авто создаст и Category
        self.assertEqual(str(channel), channel.name)

class MessageModelTest(TestCase):
    def test_str_method(self):
        message = mixer.blend(Message)
        self.assertIn(message.channel.name, str(message))
        self.assertIn(message.date.strftime("%Y-%m-%d"), str(message))

class WorkSheetModelTest(TestCase):
    def test_str_method(self):
        worksheet = mixer.blend(WorkSheet)  
        self.assertEqual(str(worksheet), worksheet.channel_name)

class ProjectModelTest(TestCase):
    def test_str_method(self):
        project = mixer.blend(Project)
        self.assertIn(project.name, str(project))
        self.assertIn(project.created_at.strftime("%Y-%m-%d"), str(project))

class RelevantChannelTest(TestCase):
    def test_str_method(self):
        relevant = mixer.blend(RelevantChannel)
        self.assertIn(relevant.project.name, str(relevant))
        self.assertIn(relevant.channel_name, str(relevant))