"""Root URL configuration for the news_project project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Template views must be included BEFORE the API to avoid
    # the API's path names shadowing the HTML views.
    path("", include("news.urls")),
    path("api/", include("news.api_urls")),
]
