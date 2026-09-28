"""
Forms for the news application.
- CustomUserCreationForm: public registration for Readers, Journalists, Editors
- ArticleForm: create/edit articles
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Registration form. New users pick a username, email, role, and password.
    The role determines their group and permissions.
    """

    email = forms.EmailField(
        required=True,
        help_text="Required. Used for article notifications.",
    )
    role = forms.ChoiceField(
        choices=CustomUser.Roles.choices,
        required=True,
        help_text="Choose your role: Reader, Journalist, or Editor.",
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "password1", "password2")

    def clean_email(self):
        """Ensure the email isn't already registered."""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        """Save the user with the chosen role. Group is auto-assigned."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()  # CustomUser.save() assigns the role group
        return user


class ArticleForm(forms.ModelForm):
    """Form used by journalists/editors to create and update articles."""

    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 10}),
        }
