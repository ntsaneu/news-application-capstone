"""
ASGI config for news_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see:
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Point Django at the project's settings module.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_project.settings")

# ASGI callable — supports async features, WebSockets, HTTP/2, etc.
application = get_asgi_application()
