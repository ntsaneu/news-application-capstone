from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Article, CustomUser, Newsletter, Publisher


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        (
            "News role",
            {
                "fields": (
                    "role",
                    "subscriptions_to_publishers",
                    "subscriptions_to_journalists",
                )
            },
        ),
    )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    filter_horizontal = ["editors", "journalists"]


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "publisher", "approved", "created_at"]
    list_filter = ["approved", "publisher"]
    search_fields = ["title", "content"]


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at"]
    filter_horizontal = ["articles"]
