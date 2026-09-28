from rest_framework import serializers

from .models import Article, CustomUser, Newsletter, Publisher


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "role",
            "subscriptions_to_publishers",
            "subscriptions_to_journalists",
        ]
        read_only_fields = ["id"]


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ["id", "name", "description", "editors", "journalists", "created_at"]
        read_only_fields = ["id", "created_at"]


class ArticleSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source="author.username")
    publisher_name = serializers.ReadOnlyField(source="publisher.name")

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "author_username",
            "publisher",
            "publisher_name",
            "created_at",
            "approved",
        ]
        read_only_fields = ["id", "created_at", "approved", "author"]

    def validate(self, attrs):
        """A journalist must supply a publisher or be the author."""
        request = self.context.get("request")
        if request and request.method == "POST":
            if not attrs.get("publisher") and not request.user.role == "journalist":
                raise serializers.ValidationError(
                    "Only journalists can create articles."
                )
        return attrs


class NewsletterSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "author",
            "author_username",
            "articles",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "author"]
