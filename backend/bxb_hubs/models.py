from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Hub(models.Model):

    class Category(models.TextChoices):
        COLLEGE = "COLLEGE", "College"
        CLUB = "CLUB", "Club"
        COMMUNITY = "COMMUNITY", "Community"
        DEPARTMENT = "DEPARTMENT", "Department"
        ORGANIZATION = "ORGANIZATION", "Organization"
        TEAM = "TEAM", "Team"
        NGO = "NGO", "NGO"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True)

    description = models.TextField(blank=True)

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.COMMUNITY,
    )

    institution = models.CharField(max_length=200, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_hubs",
    )

    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class HubMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    hub = models.ForeignKey(
        Hub,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hub_memberships",
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["joined_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["hub", "user"],
                name="unique_hub_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.hub} ({self.role})"
