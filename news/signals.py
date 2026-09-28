import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def article_approved_handler(sender, instance, created, **kwargs):
    """
    When an article is approved, notify subscribers by email and
    post to X (Twitter).
    """
    if created or not instance.approved:
        return

    # Prevent duplicate notifications using a session flag
    if getattr(instance, "_notified", False):
        return

    subscribers = instance.subscribers()
    recipient_list = [s.email for s in subscribers if s.email]

    # --- Email notification ---
    if recipient_list:
        try:
            send_mail(
                subject=f"New article: {instance.title}",
                message=(
                    f"A new article has been published.\n\n"
                    f"Title: {instance.title}\n"
                    f"Author: {instance.author.username}\n\n"
                    f"{instance.content[:500]}..."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(
                "Emailed article '%s' to %d subscribers",
                instance.title,
                len(recipient_list),
            )
        except Exception as exc:
            logger.exception("Email sending failed: %s", exc)

    # --- X (Twitter) post ---
    post_to_x(instance)

    # Mark as notified to avoid duplicate processing
    instance._notified = True


def post_to_x(article):
    """Post an approved article to X (formerly Twitter)."""
    if not settings.X_BEARER_TOKEN:
        logger.warning("X_BEARER_TOKEN not set; skipping X post.")
        return
    payload = {
        "text": f"New article published: {article.title} "
        f"by {article.author.username}"
    }
    headers = {
        "Authorization": f"Bearer {settings.X_BEARER_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            settings.X_API_URL, json=payload, headers=headers, timeout=10
        )
        response.raise_for_status()
        logger.info("Posted article '%s' to X.", article.title)
    except requests.RequestException as exc:
        logger.exception("X post failed: %s", exc)
