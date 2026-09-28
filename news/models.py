from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.core.exceptions import ValidationError


class CustomUser(AbstractUser):
    """Custom user model with role-based fields."""

    class Roles(models.TextChoices):
        READER = "reader", "Reader"
        EDITOR = "editor", "Editor"
        JOURNALIST = "journalist", "Journalist"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.READER,
        help_text="The role determines the user's permissions.",
    )

    # Reader fields
    subscriptions_to_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribers",
        help_text="Publishers this reader is subscribed to.",
    )
    subscriptions_to_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="subscribers_journalists",
        limit_choices_to={"role": "journalist"},
        help_text="Journalists this reader is subscribed to.",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def clean(self):
        """Enforce role-specific field rules."""
        super().clean()
        if self.role == self.Roles.JOURNALIST:
            # Journalists must not have reader subscriptions
            if self.pk and (
                self.subscriptions_to_publishers.exists()
                or self.subscriptions_to_journalists.exists()
            ):
                raise ValidationError("A journalist cannot have reader subscriptions.")

    def save(self, *args, **kwargs):
        """Assign the correct group based on role."""
        super().save(*args, **kwargs)
        self.assign_role_group()

    def assign_role_group(self):
        """Add the user to the correct group based on their role."""
        group_name = self.role.capitalize()
        group, _ = Group.objects.get_or_create(name=group_name)
        # Remove from other role groups
        self.groups.remove(
            *Group.objects.filter(name__in=["Reader", "Editor", "Journalist"]).exclude(
                name=group_name
            )
        )
        self.groups.add(group)


class Publisher(models.Model):
    """A publication that employs editors and journalists."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    editors = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="editor_publishers",
        limit_choices_to={"role": "editor"},
    )
    journalists = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name="journalist_publishers",
        limit_choices_to={"role": "journalist"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Article(models.Model):
    """A news article written by a journalist."""

    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="articles_published",
        limit_choices_to={"role": "journalist"},
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        """Ensure article is linked to a journalist OR a publisher."""
        super().clean()
        if not self.author and not self.publisher:
            raise ValidationError(
                "An article must be associated with a journalist or a publisher."
            )

    def subscribers(self):
        """Return all readers subscribed to this article's author or publisher."""
        from django.db.models import Q

        qs = CustomUser.objects.filter(role="reader")
        if self.publisher:
            qs = qs.filter(
                Q(subscriptions_to_publishers=self.publisher)
                | Q(subscriptions_to_journalists=self.author)
            )
        else:
            qs = qs.filter(subscriptions_to_journalists=self.author)
        return qs.distinct()


class Newsletter(models.Model):
    """A curated collection of articles."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="newsletters_published",
        limit_choices_to={"role__in": ["journalist", "editor"]},
    )
    articles = models.ManyToManyField(Article, related_name="newsletters")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
