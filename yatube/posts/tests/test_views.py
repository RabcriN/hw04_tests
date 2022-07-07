from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

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
            id=1,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа номер два',
            slug='test_slug_2',
            description='Группа для проверки поста другой группы',
        )
        Post.objects.bulk_create(
            [Post(
                author=cls.user,
                text='Тестовый пост длиной более 15 символов',
                group=Group.objects.get(slug='test_slug'),
            ) for _ in range(13)]
        )

    def setUp(self):
        self.user = User.objects.get(username='Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_context(self, page_object):
        post = Post.objects.first()
        post_data = [
            post.text,
            post.id,
            post.group.slug,
            post.author.username,
        ]
        context_data = [
            page_object.text,
            page_object.id,
            page_object.group.slug,
            page_object.author.username,
        ]
        if post_data != context_data:
            return False
        return True

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом + паджинатор
        на 10 постов"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertTrue(
            self.check_context(first_object),
            'Словари контекста не совпадают'
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом + паджинатор
        на 10 постов"""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        )
        first_object = response.context['page_obj'][0]
        self.assertTrue(
            self.check_context(first_object),
            'Словари контекста не совпадают'
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом + паджинатор
        на 10 постов"""
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Author'}))
        )
        first_object = response.context['page_obj'][0]
        self.assertTrue(
            self.check_context(first_object),
            'Словари контекста не совпадают'
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': Post.objects.first().id},
            ))
        )
        page_object = response.context['post']
        self.assertTrue(
            self.check_context(page_object),
            'Словари контекста не совпадают'
        )

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
