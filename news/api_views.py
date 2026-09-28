"""
RESTful API views for the news application.
All article endpoints, protected by role-based permissions.
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article
from .permissions import IsEditorOrJournalist, IsJournalist
from .serializers import ArticleSerializer


class ArticleListView(generics.ListAPIView):
    """GET /api/articles/ — list all approved articles."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Article.objects.filter(approved=True)


class SubscribedArticleListView(generics.ListAPIView):
    """GET /api/articles/subscribed/ — articles from the reader's subscriptions."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "reader":
            return Article.objects.none()
        publishers = user.subscriptions_to_publishers.all()
        journalists = user.subscriptions_to_journalists.all()
        return (
            Article.objects.filter(approved=True)
            .filter(Q(publisher__in=publishers) | Q(author__in=journalists))
            .distinct()
        )


class ArticleDetailView(generics.RetrieveAPIView):
    """GET /api/articles/<id>/ — retrieve a single article."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Article.objects.all()


class ArticleCreateView(generics.CreateAPIView):
    """POST /api/articles/create/ — journalists only."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsJournalist]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ArticleUpdateView(generics.UpdateAPIView):
    """PUT /api/articles/<id>/update/ — editors/journalists."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsEditorOrJournalist]
    queryset = Article.objects.all()


class ArticleDeleteView(generics.DestroyAPIView):
    """DELETE /api/articles/<id>/delete/ — editors/journalists."""

    permission_classes = [IsAuthenticated, IsEditorOrJournalist]
    queryset = Article.objects.all()


class ArticleApproveView(APIView):
    """POST /api/articles/<id>/approve/ — editors only."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != "editor":
            return Response(
                {"detail": "Only editors can approve articles."},
                status=status.HTTP_403_FORBIDDEN,
            )
        article = get_object_or_404(Article, pk=pk)
        article.approved = True
        article.save()  # triggers post_save signal
        return Response(
            {"detail": "Article approved.", "id": article.id},
            status=status.HTTP_200_OK,
        )
