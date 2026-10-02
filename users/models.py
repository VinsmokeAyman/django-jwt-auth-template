# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("tier1", "Tier 1"),
        ("tier2", "Tier 2"),
        ("tier3", "Tier 3"),
    ]

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="tier3"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    fullName = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.email

