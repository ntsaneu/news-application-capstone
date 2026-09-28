"""
Template-based views for the news application.

Handles HTML rendering for readers, journalists, and editors.
"""

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ArticleForm, CustomUserCreationForm
from .models import Article

# ---------------------------------------------------------------------------
# Home & authentication
# ---------------------------------------------------------------------------


def home(request):
    """Landing page for all visitors."""
    return render(request, "news/home.html")


def register(request):
    """
    Public registration view.

    Creates a user with the chosen role and auto-logs them in.
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomUserCreationForm()

    return render(request, "news/register.html", {"form": form})


# ---------------------------------------------------------------------------
# Article views
# ---------------------------------------------------------------------------


def article_list(request):
    """Anyone can browse approved articles."""
    articles = Article.objects.filter(approved=True)
    return render(request, "news/article_list.html", {"articles": articles})


def article_detail(request, pk):
    """View a single article. Pending articles only visible to staff."""
    article = get_object_or_404(Article, pk=pk)

    if not article.approved and (
        not request.user.is_authenticated
        or request.user.role not in ["editor", "journalist"]
    ):
        raise PermissionDenied

    return render(request, "news/article_detail.html", {"article": article})


@login_required
def article_create(request):
    """
    Journalists create new articles via an HTML form.

    GET  → render the empty form
    POST → validate and save, then redirect to the detail page

    IMPORTANT: The author is assigned to ``form.instance`` BEFORE
    calling ``form.is_valid()`` so that the model's ``clean()`` method
    (which requires either an author or a publisher) doesn't fail
    with a RelatedObjectDoesNotExist error.
    """
    if request.user.role != "journalist":
        raise PermissionDenied

    if request.method == "POST":
        form = ArticleForm(request.POST)
        # Assign the author BEFORE validation.
        form.instance.author = request.user
        if form.is_valid():
            article = form.save()
            return redirect("article-detail", pk=article.pk)
    else:
        form = ArticleForm()
        # Also set on GET so the instance is consistent.
        form.instance.author = request.user

    return render(request, "news/article_form.html", {"form": form})


@login_required
def article_edit(request, pk):
    """Editors and journalists can edit articles."""
    if request.user.role not in ["editor", "journalist"]:
        raise PermissionDenied

    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect("article-detail", pk=article.pk)
    else:
        form = ArticleForm(instance=article)

    return render(request, "news/article_form.html", {"form": form})


@login_required
def pending_articles(request):
    """Editors review unapproved articles."""
    if request.user.role != "editor":
        raise PermissionDenied

    articles = Article.objects.filter(approved=False)
    return render(
        request,
        "news/pending_articles.html",
        {"articles": articles},
    )


@login_required
def approve_article(request, pk):
    """Editor approves an article (fires the post_save signal)."""
    if request.user.role != "editor":
        raise PermissionDenied

    article = get_object_or_404(Article, pk=pk)
    article.approved = True
    article.save()  # signal fires: emails subscribers + posts to X

    return redirect("pending-articles")
