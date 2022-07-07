from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.create(
            text='Тестовый текст длиной более 15 символов',
            author=User.objects.create_user(username='Author'),
            group=Group.objects.create(
                title='test title',
                slug='test_slug',
                description='test description',
            )
        )
        cls.guest_templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test_slug/',
            'posts/profile.html': '/profile/Not_Author/',
            'posts/post_detail.html': '/posts/1/',
        }
        cls.auth_templates_url_names = cls.guest_templates_url_names.copy()
        only_auth_links = {'posts/post_create.html': '/create/'}
        cls.auth_templates_url_names.update(only_auth_links)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Not_Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user2 = User.objects.get(username='Author')
        self.client_is_author = Client()
        self.client_is_author.force_login(self.user2)

    def test_urls_uses_correct_template_for_anonymous(self):
        """URL-адрес использует соответствующий шаблон.
        Пользователь не авторизирован"""
        for template, address in self.guest_templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_authorized(self):
        """URL-адрес использует соответствующий шаблон.
        Пользователь авторизирован"""
        for template, address in self.auth_templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_create_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_page_doesnt_exist(self):
        """Несуществующая страница выдаёт 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_edit_page_if_not_author(self):
        """Страница /edit/ редиректит, если юзер не автор поста"""
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_edit_page_if_is_author(self):
        """Страница /edit/ открывает шаблон create автору поста"""
        response = self.client_is_author.get('/posts/1/edit/')
        self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_guest_goes_to_links(self):
        """Неавторизированный пользователь ходит по ссылкам"""
        for address in self.guest_templates_url_names.values():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_auth_goes_to_links(self):
        """Авторизированный пользователь ходит по ссылкам"""
        for address in self.auth_templates_url_names.values():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)
