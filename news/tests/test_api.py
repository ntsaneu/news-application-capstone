"""
Automated unit tests for the News Application RESTful API.

Covers:
- Authenticated access per role
- Reader retrieves only subscribed content
- Journalist can create articles
- Editor can approve and delete
- Reader cannot create/approve/delete
- Successful and failed request examples
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from news.models import Article, CustomUser, Newsletter, Publisher


def authenticate(client, user):
    """Attach a valid JWT access token to the APIClient."""
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class BaseAPITestCase(APITestCase):
    """Shared setup for all API tests."""

    def setUp(self):
        # Publishers
        self.publisher = Publisher.objects.create(name="Tech Times")
        self.other_publisher = Publisher.objects.create(name="Daily Sports")

        # Users by role
        self.journalist = CustomUser.objects.create_user(
            username="jane",
            password="pass1234",
            role="journalist",
            email="jane@example.com",
        )
        self.other_journalist = CustomUser.objects.create_user(
            username="john",
            password="pass1234",
            role="journalist",
            email="john@example.com",
        )
        self.reader = CustomUser.objects.create_user(
            username="bob",
            password="pass1234",
            role="reader",
            email="bob@example.com",
        )
        self.editor = CustomUser.objects.create_user(
            username="ed",
            password="pass1234",
            role="editor",
            email="ed@example.com",
        )

        # Publisher memberships
        self.publisher.journalists.add(self.journalist)
        self.publisher.editors.add(self.editor)
        self.other_publisher.journalists.add(self.other_journalist)

        # Reader subscribes to the first journalist & first publisher
        self.reader.subscriptions_to_journalists.add(self.journalist)
        self.reader.subscriptions_to_publishers.add(self.publisher)

        # Articles — one approved (subscribed), one approved (not subscribed),
        # one pending
        self.approved_article = Article.objects.create(
            title="Approved Subscribed",
            content="Body A",
            author=self.journalist,
            publisher=self.publisher,
            approved=True,
        )
        self.other_article = Article.objects.create(
            title="Approved Other",
            content="Body B",
            author=self.other_journalist,
            publisher=self.other_publisher,
            approved=True,
        )
        self.pending_article = Article.objects.create(
            title="Pending",
            content="Body C",
            author=self.journalist,
            publisher=self.publisher,
            approved=False,
        )


class AuthenticationTests(BaseAPITestCase):
    """Tests around authentication and token handling."""

    def test_unauthenticated_list_returns_401(self):
        response = self.client.get(reverse("api-article-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_endpoint_returns_access_and_refresh(self):
        response = self.client.post(
            reverse("api-token-obtain"),
            {"username": "bob", "password": "pass1234"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_endpoint_wrong_password(self):
        response = self.client.post(
            reverse("api-token-obtain"),
            {"username": "bob", "password": "WRONG"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_list_returns_200(self):
        authenticate(self.client, self.reader)
        response = self.client.get(reverse("api-article-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ArticleListTests(BaseAPITestCase):
    """GET /api/articles/ — only approved articles should appear."""

    def test_list_only_returns_approved_articles(self):
        authenticate(self.client, self.reader)
        response = self.client.get(reverse("api-article-list"))
        titles = [a["title"] for a in response.data["results"]]
        self.assertIn("Approved Subscribed", titles)
        self.assertIn("Approved Other", titles)
        self.assertNotIn("Pending", titles)

    def test_article_detail_returns_single_article(self):
        authenticate(self.client, self.reader)
        response = self.client.get(
            reverse("api-article-detail", args=[self.approved_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Approved Subscribed")

    def test_article_detail_missing_returns_404(self):
        authenticate(self.client, self.reader)
        response = self.client.get(reverse("api-article-detail", args=[99999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubscribedArticleTests(BaseAPITestCase):
    """GET /api/articles/subscribed/ — filtered by reader subscriptions."""

    def test_reader_sees_only_subscribed_articles(self):
        authenticate(self.client, self.reader)
        response = self.client.get(reverse("api-article-subscribed"))
        titles = [a["title"] for a in response.data["results"]]

        self.assertIn("Approved Subscribed", titles)
        self.assertNotIn("Approved Other", titles)  # not subscribed
        self.assertNotIn("Pending", titles)  # not approved

    def test_non_reader_gets_empty_subscribed_list(self):
        authenticate(self.client, self.editor)
        response = self.client.get(reverse("api-article-subscribed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])

    def test_journalist_gets_empty_subscribed_list(self):
        authenticate(self.client, self.journalist)
        response = self.client.get(reverse("api-article-subscribed"))
        self.assertEqual(response.data["results"], [])


class ArticleCreateTests(BaseAPITestCase):
    """POST /api/articles/create/ — journalists only."""

    def test_journalist_can_create_article(self):
        authenticate(self.client, self.journalist)
        payload = {
            "title": "Brand New",
            "content": "Fresh content",
            "publisher": self.publisher.id,
        }
        response = self.client.post(reverse("api-article-create"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Brand New")
        # Author is auto-assigned
        self.assertEqual(
            Article.objects.get(id=response.data["id"]).author,
            self.journalist,
        )

    def test_reader_cannot_create_article(self):
        authenticate(self.client, self.reader)
        payload = {"title": "Nope", "content": "x"}
        response = self.client.post(reverse("api-article-create"), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_cannot_create_article(self):
        authenticate(self.client, self.editor)
        payload = {"title": "Nope", "content": "x"}
        response = self.client.post(reverse("api-article-create"), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_article(self):
        payload = {"title": "Nope", "content": "x"}
        response = self.client.post(reverse("api-article-create"), payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_article_missing_title_fails(self):
        authenticate(self.client, self.journalist)
        payload = {"content": "no title here"}
        response = self.client.post(reverse("api-article-create"), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)


class ArticleUpdateTests(BaseAPITestCase):
    """PUT /api/articles/<id>/update/ — editors and journalists only."""

    def test_journalist_can_update_article(self):
        authenticate(self.client, self.journalist)
        response = self.client.put(
            reverse("api-article-update", args=[self.approved_article.id]),
            {"title": "Updated", "content": "Updated body"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.approved_article.refresh_from_db()
        self.assertEqual(self.approved_article.title, "Updated")

    def test_editor_can_update_article(self):
        authenticate(self.client, self.editor)
        response = self.client.put(
            reverse("api-article-update", args=[self.approved_article.id]),
            {"title": "Editor Edited", "content": "…"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reader_cannot_update_article(self):
        authenticate(self.client, self.reader)
        response = self.client.put(
            reverse("api-article-update", args=[self.approved_article.id]),
            {"title": "Hacked", "content": "…"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ArticleDeleteTests(BaseAPITestCase):
    """DELETE /api/articles/<id>/delete/ — editors and journalists only."""

    def test_editor_can_delete_article(self):
        authenticate(self.client, self.editor)
        response = self.client.delete(
            reverse("api-article-delete", args=[self.approved_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=self.approved_article.id).exists())

    def test_journalist_can_delete_article(self):
        authenticate(self.client, self.journalist)
        response = self.client.delete(
            reverse("api-article-delete", args=[self.approved_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_reader_cannot_delete_article(self):
        authenticate(self.client, self.reader)
        response = self.client.delete(
            reverse("api-article-delete", args=[self.approved_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Article.objects.filter(id=self.approved_article.id).exists())


class ArticleApproveTests(BaseAPITestCase):
    """POST /api/articles/<id>/approve/ — editors only."""

    def test_editor_can_approve_pending_article(self):
        authenticate(self.client, self.editor)
        response = self.client.post(
            reverse("api-article-approve", args=[self.pending_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)

    def test_journalist_cannot_approve(self):
        authenticate(self.client, self.journalist)
        response = self.client.post(
            reverse("api-article-approve", args=[self.pending_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.pending_article.refresh_from_db()
        self.assertFalse(self.pending_article.approved)

    def test_reader_cannot_approve(self):
        authenticate(self.client, self.reader)
        response = self.client.post(
            reverse("api-article-approve", args=[self.pending_article.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_missing_article_returns_404(self):
        authenticate(self.client, self.editor)
        response = self.client.post(reverse("api-article-approve", args=[99999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NewsletterAPITests(BaseAPITestCase):
    """Tests for the Newsletter model & its relation to Articles."""

    def setUp(self):
        super().setUp()
        self.newsletter = Newsletter.objects.create(
            title="Weekly Digest",
            description="Top stories this week.",
            author=self.journalist,
        )
        self.newsletter.articles.add(self.approved_article)

    def test_newsletter_contains_article(self):
        self.assertIn(self.approved_article, self.newsletter.articles.all())

    def test_newsletter_deleted_when_author_deleted(self):
        nl_id = self.newsletter.id
        self.journalist.delete()
        self.assertFalse(Newsletter.objects.filter(id=nl_id).exists())
