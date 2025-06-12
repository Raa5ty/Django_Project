from django.test import TestCase
from tgservice.forms import ProjectForm

class ProjectFormTests(TestCase):
    def setUp(self):
        self.valid_data = {
            'name': 'Test Project',
            'description': 'Project description',
            'target_audience': 'Entrepreneurs',
            'keywords': 'AI, Telegram',
            'count_requested': 5
            # 'creatives' опущено — поле должно быть необязательным
        }

    def test_form_is_valid_with_required_fields_only(self):
        form = ProjectForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_form_is_invalid_without_name(self):
        data = self.valid_data.copy()
        data.pop('name')
        form = ProjectForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_creatives_field_is_not_required(self):
        form = ProjectForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.fields['creatives'].required)