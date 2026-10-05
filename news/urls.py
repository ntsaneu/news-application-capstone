"""URL routing for the news application.

Maps URL paths to HTML template views for home, authentication,
article browsing, creation, editing, and editorial approval.
""

"""URL patterns for the news application (HTML template views)."""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),
    # Authentication
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="news/login.html"),
        name="login",
    ),
    path("register/", views.register, name="register"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Article views (HTML)
    path("articles/", views.article_list, name="article-list"),
    path("articles/create/", views.article_create, name="article-create"),
    path("articles/pending/", views.pending_articles, name="pending-articles"),
    path("articles/<int:pk>/", views.article_detail, name="article-detail"),
    path("articles/<int:pk>/edit/", views.article_edit, name="article-edit"),
    path(
        "articles/<int:pk>/approve/",
        views.approve_article,
        name="approve-article",
    ),
]
