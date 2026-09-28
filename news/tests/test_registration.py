"""
Tests for the public registration flow.
Verifies that anyone can register as Reader, Journalist, or Editor,
and that the correct group is auto-assigned.
"""

from django.test import TestCase
from django.urls import reverse

from news.models import CustomUser


class RegistrationTests(TestCase):
    """Public registration should work for all three roles."""

    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create an Account")

    def test_reader_can_register(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newreader",
                "email": "reader@example.com",
                "role": "reader",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 302)  # redirect on success
        user = CustomUser.objects.get(username="newreader")
        self.assertEqual(user.role, "reader")
        self.assertIn("Reader", [g.name for g in user.groups.all()])

    def test_journalist_can_register(self):
        self.client.post(
            reverse("register"),
            {
                "username": "newjournalist",
                "email": "journalist@example.com",
                "role": "journalist",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        user = CustomUser.objects.get(username="newjournalist")
        self.assertEqual(user.role, "journalist")
        self.assertIn("Journalist", [g.name for g in user.groups.all()])

    def test_editor_can_register(self):
        self.client.post(
            reverse("register"),
            {
                "username": "neweditor",
                "email": "editor@example.com",
                "role": "editor",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        user = CustomUser.objects.get(username="neweditor")
        self.assertEqual(user.role, "editor")
        self.assertIn("Editor", [g.name for g in user.groups.all()])

    def test_register_with_duplicate_email_fails(self):
        CustomUser.objects.create_user(
            username="existing",
            email="taken@example.com",
            password="pass1234",
        )
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "taken@example.com",
                "role": "reader",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)  # re-renders with error
        self.assertContains(response, "already exists")

    def test_register_with_mismatched_passwords_fails(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "role": "reader",
                "password1": "ComplexPass123!",
                "password2": "DifferentPass456!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="newuser").exists())
