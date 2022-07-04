from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post
from django import forms

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа номер два',
            slug='test_slug_2',
            description='Группа для проверки поста другой группы',
        )
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост длиной более 15 символов',
                group=Group.objects.get(slug='test_slug'),
            )

    def setUp(self):
        self.user = User.objects.get(username='Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}): (
                'posts/group_list.html'),
            reverse('posts:profile', kwargs={'username': 'Author'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': '1'}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit', kwargs={'post_id': '1'}): (
                'posts/post_create.html'
            ),
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом + паджинатор
        на 10 постов"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый пост длиной более 15 символов')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом + паджинатор
        на 10 постов"""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, 'Тестовый пост длиной более 15 символов')
        self.assertEqual(
            response.context.get('group').title,
            'Тестовая группа'
        )
        self.assertEqual(response.context.get('group').slug, 'test_slug')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом + паджинатор
        на 10 постов"""
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Author'}))
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        self.assertEqual(post_text_0, 'Тестовый пост длиной более 15 символов')
        self.assertEqual(post_author_0, 'Author')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        )
        page_object = response.context['post']
        post_text_0 = page_object.text
        post_id_0 = page_object.id
        self.assertEqual(post_text_0, 'Тестовый пост длиной более 15 символов')
        self.assertEqual(post_id_0, 1)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:post_create')))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        page_object = response.context['post']
        post_id_0 = page_object.id
        self.assertEqual(post_id_0, 1)

    def test_created_post_not_in_another_group(self):
        """Проверяем, что пост не попал в другую группу"""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_2'}))
        )
        self.assertEqual(len(response.context['page_obj']), 0)
        for post in Post.objects.all():
            self.assertEqual(post.group.slug, 'test_slug')
