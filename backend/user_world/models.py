from django.db import models

# Create your models here.

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class World(models.Model):
    """A user-created world inside BxB."""

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    class JoinPolicy(models.TextChoices):
        OPEN = "open", "Anyone can join"
        APPROVAL = "approval", "Approval required"
        INVITE = "invite", "Invite only"

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(max_length=2000, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_worlds",
    )

    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )

    join_policy = models.CharField(
        max_length=10,
        choices=JoinPolicy.choices,
        default=JoinPolicy.OPEN,
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="WorldMembership",
        related_name="world_memberships",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "world"
            candidate = base_slug
            counter = 2

            while World.objects.filter(slug=candidate).exclude(
                pk=self.pk
            ).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1

            self.slug = candidate

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class WorldMembership(models.Model):
    """Membership and permissions within a world."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MODERATOR = "moderator", "Moderator"
        MEMBER = "member", "Member"

    world = models.ForeignKey(
        World,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="world_memberships_as_member",
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
                fields=["world", "user"],
                name="unique_world_membership",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.world} ({self.role})"


class WorldPost(models.Model):
    """A post published inside a world."""

    world = models.ForeignKey(
        World,
        on_delete=models.CASCADE,
        related_name="posts",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="world_posts",
    )

    content = models.TextField(max_length=10000)
    is_pinned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return f"Post in {self.world} by {self.author}"


class WorldJoinRequest(models.Model):
    """Tracks requests to join worlds that require approval."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    world = models.ForeignKey(
        World,
        on_delete=models.CASCADE,
        related_name="join_requests",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="world_join_requests",
    )

    message = models.CharField(max_length=500, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["world", "user"],
                name="unique_world_join_request",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.world} ({self.status})"
