from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Channel(models.Model):
    class Category(models.TextChoices):
        COLLEGE = "college", "College"
        CLUB = "club", "Club or Society"
        COMMUNITY = "community", "Community"
        DEPARTMENT = "department", "Department"
        ORGANIZATION = "organization", "Organization"
        OTHER = "other", "Other"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(max_length=1500)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.COMMUNITY,
    )
    college = models.CharField(max_length=150, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_channels",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ChannelMembership",
        related_name="joined_channels",
    )

    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ChannelMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel_memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"],
                name="unique_channel_membership",
            )
        ]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.username} — {self.channel.name} ({self.role})"


class ChannelAnnouncement(models.Model):
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel_announcements",
    )
    title = models.CharField(max_length=150)
    body = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.channel.name}"
