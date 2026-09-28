"""
Automated tests for the article-approval signal logic.

Verifies:
- Email is sent to subscribers when an article is approved
- No email is sent when an unapproved article is created
- X (Twitter) post is triggered (mocked)
- Signal does not fire twice for the same article
"""

from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from news.models import Article, CustomUser, Publisher


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    X_BEARER_TOKEN="test-token",
    X_API_URL="https://api.twitter.com/2/tweets",
)
class ArticleApprovalSignalTests(TestCase):
    """Tests for the post_save signal on Article."""

    def setUp(self):
        self.publisher = Publisher.objects.create(name="Daily News")
        self.journalist = CustomUser.objects.create_user(
            username="jane",
            password="pass1234",
            role="journalist",
            email="jane@example.com",
        )
        self.reader = CustomUser.objects.create_user(
            username="bob",
            password="pass1234",
            role="reader",
            email="bob@example.com",
        )
        self.other_reader = CustomUser.objects.create_user(
            username="alice",
            password="pass1234",
            role="reader",
            email="alice@example.com",
        )

        # Bob subscribes to the journalist, Alice does not
        self.reader.subscriptions_to_journalists.add(self.journalist)

        # Clear any emails sent during setup
        mail.outbox = []

    # ----------------------------------------------------------------
    # Email tests
    # ----------------------------------------------------------------

    @patch("news.signals.post_to_x")
    def test_email_sent_to_subscribers_on_approval(self, mock_post):
        article = Article.objects.create(
            title="Breaking News",
            content="Something happened.",
            author=self.journalist,
        )
        mail.outbox = []  # reset after creation (not yet approved)

        article.approved = True
        article.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("bob@example.com", mail.outbox[0].to)
        self.assertNotIn("alice@example.com", mail.outbox[0].to)
        self.assertIn("Breaking News", mail.outbox[0].subject)

    @patch("news.signals.post_to_x")
    def test_no_email_when_article_not_approved(self, mock_post):
        Article.objects.create(
            title="Draft",
            content="Still in review.",
            author=self.journalist,
        )
        self.assertEqual(len(mail.outbox), 0)

    @patch("news.signals.post_to_x")
    def test_email_includes_publisher_subscribers(self, mock_post):
        self.publisher.journalists.add(self.journalist)
        self.other_reader.subscriptions_to_publishers.add(self.publisher)

        article = Article.objects.create(
            title="Publisher Article",
            content="x",
            author=self.journalist,
            publisher=self.publisher,
        )
        mail.outbox = []

        article.approved = True
        article.save()

        # Bob (journalist subscriber) + Alice (publisher subscriber)
        recipients = [addr for m in mail.outbox for addr in m.to]
        self.assertIn("bob@example.com", recipients)
        self.assertIn("alice@example.com", recipients)

    @patch("news.signals.post_to_x")
    def test_no_email_when_no_subscribers(self, mock_post):
        lonely_journalist = CustomUser.objects.create_user(
            username="lonely",
            password="pass1234",
            role="journalist",
            email="lonely@example.com",
        )
        article = Article.objects.create(
            title="Unread",
            content="No one is subscribed.",
            author=lonely_journalist,
        )
        mail.outbox = []

        article.approved = True
        article.save()

        self.assertEqual(len(mail.outbox), 0)

    # ----------------------------------------------------------------
    # X (Twitter) tests
    # ----------------------------------------------------------------

    @patch("news.signals.post_to_x")
    def test_x_post_called_on_approval(self, mock_post_to_x):
        article = Article.objects.create(
            title="Tweet Me",
            content="x",
            author=self.journalist,
        )
        article.approved = True
        article.save()

        mock_post_to_x.assert_called_once()
        # The article argument is passed positionally
        args, _kwargs = mock_post_to_x.call_args
        self.assertEqual(args[0].id, article.id)

    @patch("news.signals.post_to_x")
    def test_x_post_not_called_for_unapproved_article(self, mock_post_to_x):
        Article.objects.create(
            title="Draft",
            content="x",
            author=self.journalist,
        )
        mock_post_to_x.assert_not_called()

    # ----------------------------------------------------------------
    # Real HTTP behaviour (mocked at the requests level)
    # ----------------------------------------------------------------

    @patch("news.signals.requests.post")
    def test_post_to_x_sends_correct_payload(self, mock_requests_post):
        """Verify the actual post_to_x function sends the correct JSON."""
        from news.signals import post_to_x

        article = Article.objects.create(
            title="Hello World",
            content="x",
            author=self.journalist,
        )

        post_to_x(article)

        mock_requests_post.assert_called_once()
        _args, kwargs = mock_requests_post.call_args
        self.assertIn("Hello World", kwargs["json"]["text"])
        self.assertIn("jane", kwargs["json"]["text"])
        self.assertIn("Authorization", kwargs["headers"])
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("Bearer "))

    @patch("news.signals.requests.post")
    def test_post_to_x_handles_request_exception(self, mock_requests_post):
        """If X API fails, the exception is caught and logged (no crash)."""
        import requests
        from news.signals import post_to_x

        mock_requests_post.side_effect = requests.RequestException("boom")

        article = Article.objects.create(
            title="Fail safe",
            content="x",
            author=self.journalist,
        )
        # Should not raise
        post_to_x(article)

    @override_settings(X_BEARER_TOKEN="")
    @patch("news.signals.requests.post")
    def test_post_to_x_skipped_when_no_token(self, mock_requests_post):
        """If X_BEARER_TOKEN is empty, no HTTP call is made."""
        from news.signals import post_to_x

        article = Article.objects.create(
            title="No token",
            content="x",
            author=self.journalist,
        )
        post_to_x(article)
        mock_requests_post.assert_not_called()
