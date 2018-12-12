from django.http import HttpRequest
from django.test import SimpleTestCase
from django.urls import reverse

from users import views


class ProjectsPageTests(SimpleTestCase):

    def test_projects_page_status_code(self):
        response = self.client.get('/projects/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_by_name(self):
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects.html')

    # def test_projects_page_contains_correct_html(self):
    #     response = self.client.get('/about/')
    #     self.assertContains(response, '<h1>Projects page</h1>')

    def test_projects_page_does_not_contain_incorrect_html(self):
        response = self.client.get('/')
        self.assertNotContains(
            response, 'Hi there! I should not be on the page.')
