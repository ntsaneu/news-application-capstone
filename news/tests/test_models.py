from django.test import TestCase

from news.models import Article, CustomUser, Publisher


class ModelTests(TestCase):
    def setUp(self):
        self.publisher = Publisher.objects.create(name="Daily News")
        self.journalist = CustomUser.objects.create_user(
            username="jane", password="pass1234", role="journalist"
        )
        self.reader = CustomUser.objects.create_user(
            username="bob", password="pass1234", role="reader"
        )

    def test_article_created(self):
        article = Article.objects.create(
            title="Hello", content="World", author=self.journalist
        )
        self.assertEqual(article.title, "Hello")
        self.assertFalse(article.approved)

    def test_subscribers_returns_correct_readers(self):
        self.reader.subscriptions_to_journalists.add(self.journalist)
        article = Article.objects.create(title="A", content="B", author=self.journalist)
        self.assertIn(self.reader, article.subscribers())

    def test_user_group_assignment(self):
        self.assertIn("Journalist", [g.name for g in self.journalist.groups.all()])
        self.assertIn("Reader", [g.name for g in self.reader.groups.all()])
