from django.http import HttpRequest
from django.test import SimpleTestCase
from django.urls import reverse

from users import views


class LoginPageTests(SimpleTestCase):

    def test_login_page_status_code(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_by_name(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    # def test_login_page_contains_correct_html(self):
    #     response = self.client.get('/about/')
    #     self.assertContains(response, '<h1>Login page</h1>')

    def test_login_page_does_not_contain_incorrect_html(self):
        response = self.client.get('/')
        self.assertNotContains(
            response, 'Hi there! I should not be on the page.')
