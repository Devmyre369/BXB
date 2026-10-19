
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}


def vibe_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"vibes/{uuid.uuid4().hex}{extension}"


def validate_vibe_media(file):
    extension = Path(file.name).suffix.lower()

    if extension not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS:
        raise ValidationError(
            "Upload an image, GIF, or supported video file."
        )

    is_video = extension in VIDEO_EXTENSIONS
    max_size = (
        200 * 1024 * 1024
        if is_video
        else 10 * 1024 * 1024
    )

    if file.size > max_size:
        raise ValidationError(
            "Images and GIFs must be at most 10 MB. "
            "Videos must be at most 200 MB."
        )


class Vibe(models.Model):
    class TargetAudience(models.TextChoices):
        EVERYONE = "everyone", "Everyone"
        MY_CAMPUS = "my_campus", "My campus"
        STUDENTS = "students", "Students"
        DEVELOPERS = "developers", "Developers"
        DESIGNERS = "designers", "Designers"
        EVENT_PARTICIPANTS = (
            "event_participants",
            "Event participants",
        )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibes",
    )

    media = models.FileField(
        upload_to=vibe_upload_path,
        validators=[validate_vibe_media],
        max_length=255,
    )

    caption = models.CharField(max_length=500, blank=True)

    description = models.TextField(
        max_length=1500,
        blank=True,
    )

    tags = models.ManyToManyField(
        "VibeTag",
        blank=True,
        related_name="vibes",
    )

    is_campus_event = models.BooleanField(default=False)

    campus_event_name = models.CharField(
        max_length=200,
        blank=True,
    )

    target_audience = models.CharField(
        max_length=30,
        choices=TargetAudience.choices,
        default=TargetAudience.EVERYONE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    is_public = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_video(self):
        return Path(self.media.name).suffix.lower() in VIDEO_EXTENSIONS

    def __str__(self):
        return f"Vibe by {self.author.username} (#{self.pk})"


class VibeTag(models.Model):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"


class VibeLike(models.Model):
    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        related_name="likes",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibe_likes",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vibe", "user"],
                name="unique_vibe_like_per_user",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} likes Vibe #{self.vibe_id}"


class VibeRepost(models.Model):
    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        related_name="reposts",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibe_reposts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vibe", "user"],
                name="unique_vibe_repost_per_user",
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} revibed Vibe #{self.vibe_id}"


class VibeComment(models.Model):
    vibe = models.ForeignKey(
        Vibe,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vibe_comments",
    )

    text = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user} on Vibe #{self.vibe_id}"
