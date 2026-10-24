'''

from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Notification(models.Model):

    class NotificationType(models.TextChoices):

        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        REPOST = "repost", "Repost"

        HANDSHAKE_RECEIVED = (
            "handshake_received",
            "Handshake Received"
        )

        HANDSHAKE_ACCEPTED = (
            "handshake_accepted",
            "Handshake Accepted"
        )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_created"
    )

    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices
    )

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    handshake = models.ForeignKey(
        "handshake.Handshake",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    comment = models.ForeignKey(
        "posts.Comment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    message = models.CharField(
        max_length=255,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):

        return (
            f"{self.actor.username} → "
            f"{self.recipient.username}: "
            f"{self.notification_type}"
        )

        '''

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import NoReverseMatch, reverse


class Notification(models.Model):
    """
    One row per notification shown in a user's in-app inbox.

    The row is the single source of truth. Email delivery (optional) is
    layered on top of it in notifications.services.
    """

    class NotificationType(models.TextChoices):
        # Existing values are unchanged so old rows stay valid.
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        REPOST = "repost", "Revibe"
        HANDSHAKE_RECEIVED = "handshake_received", "Handshake Received"
        HANDSHAKE_ACCEPTED = "handshake_accepted", "Handshake Accepted"

        # New in the full notification system.
        SAVE = "save", "Save"
        SHARE = "share", "Share"
        FOLLOW = "follow", "Follow"
        EVENT_NEW = "event_new", "New Event"
        EVENT_REGISTRATION = "event_registration", "Event Registration"
        EVENT_TEAM_JOIN = "event_team_join", "Event Team Join"
        EVENT_CANCELLED = "event_cancelled", "Event Cancelled"
        WORLD_JOIN = "world_join", "World Join"
        WORLD_ANNOUNCEMENT = "world_announcement", "World Announcement"
        MESSAGE = "message", "Message"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications_created",
    )

    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
    )

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    handshake = models.ForeignKey(
        "handshake.Handshake",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    comment = models.ForeignKey(
        "posts.Comment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    vibe = models.ForeignKey(
        "vibespace.Vibe",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    vibe_comment = models.ForeignKey(
        "vibespace.VibeComment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )

    # Generic target for things without a dedicated FK yet
    # (Worlds/channels, direct messages, future features).
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    message = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="notif_inbox_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.actor.username} → "
            f"{self.recipient.username}: "
            f"{self.notification_type}"
        )

    def get_target_url(self):
        """Best link for this notification, or '' if none applies."""
        T = self.NotificationType
        try:
            if self.vibe_id:
                return reverse("vibespace:detail", args=[self.vibe_id])

            if self.post_id:
                return f"{reverse('feed')}#post-{self.post_id}"

            if self.event_id:
                return reverse("events:event_detail", args=[self.event.slug])

            if self.notification_type in (
                T.FOLLOW,
                T.HANDSHAKE_RECEIVED,
                T.HANDSHAKE_ACCEPTED,
            ):
                return reverse("public_profile", args=[self.actor.username])

            target = self.target
            if target is not None and hasattr(target, "get_absolute_url"):
                return target.get_absolute_url()
        except NoReverseMatch:
            return ""
        return ""


class NotificationPreference(models.Model):
    """
    Per-user, per-type delivery choices.

    A missing row means "use the defaults" (see services.DEFAULT_EMAIL_TYPES):
    in-app on, email only for the important types.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    notification_type = models.CharField(
        max_length=40,
        choices=Notification.NotificationType.choices,
    )
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "notification_type"],
                name="unique_notification_pref_per_type",
            )
        ]

    def __str__(self):
        return f"{self.user.username}: {self.notification_type}"


class ContentShare(models.Model):
    """
    Records that a user shared a Post or a Vibe, so the author can be
    notified. (Sharing itself still happens in the browser.)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="content_shares",
    )
    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shares",
    )
    vibe = models.ForeignKey(
        "vibespace.Vibe",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shares",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(post__isnull=False, vibe__isnull=True)
                    | models.Q(post__isnull=True, vibe__isnull=False)
                ),
                name="share_exactly_one_target",
            )
        ]

    def __str__(self):
        target = f"post {self.post_id}" if self.post_id else f"vibe {self.vibe_id}"
        return f"{self.user.username} shared {target}"