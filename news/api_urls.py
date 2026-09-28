"""
URL patterns for the RESTful API.

All URL names are prefixed with ``api-`` to prevent collisions with the
template view names defined in ``news/urls.py``.
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import api_views

urlpatterns = [
    # Authentication
    path("token/", TokenObtainPairView.as_view(), name="api-token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    # Articles
    path(
        "articles/",
        api_views.ArticleListView.as_view(),
        name="api-article-list",
    ),
    path(
        "articles/subscribed/",
        api_views.SubscribedArticleListView.as_view(),
        name="api-article-subscribed",
    ),
    path(
        "articles/create/",
        api_views.ArticleCreateView.as_view(),
        name="api-article-create",
    ),
    path(
        "articles/<int:pk>/",
        api_views.ArticleDetailView.as_view(),
        name="api-article-detail",
    ),
    path(
        "articles/<int:pk>/update/",
        api_views.ArticleUpdateView.as_view(),
        name="api-article-update",
    ),
    path(
        "articles/<int:pk>/delete/",
        api_views.ArticleDeleteView.as_view(),
        name="api-article-delete",
    ),
    path(
        "articles/<int:pk>/approve/",
        api_views.ArticleApproveView.as_view(),
        name="api-article-approve",
    ),
]
