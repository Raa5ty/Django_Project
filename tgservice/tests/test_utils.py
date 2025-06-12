from django.test import TestCase
from tgservice.models import Project, RelevantChannel
from tgservice.utils import generate_excel_for_project
import pandas as pd

class GenerateExcelForProjectTests(TestCase):

    def test_returns_none_if_no_channels(self):
        project = Project.objects.create(name="Test Project")
        result = generate_excel_for_project(project)
        self.assertIsNone(result)

    def test_returns_excel_file_with_correct_data(self):
        project = Project.objects.create(name="Test Project")

        RelevantChannel.objects.create(
            project=project,
            channel_name="Test Channel",
            category="Education",
            subscribers=1000,
            title="Some Title",
            description="Some Desc",
            last_post_date="2024-01-01",
            profile_channel="Profile",
            keywords_channel="AI, ML",
            score=9.5,
            new_creatives="Creative Text"
        )

        result = generate_excel_for_project(project)
        self.assertIsNotNone(result)

        result.seek(0)
        df = pd.read_excel(result)

        self.assertEqual(df.shape[0], 1)
        self.assertEqual(df.iloc[0]["Название канала"], "Test Channel")