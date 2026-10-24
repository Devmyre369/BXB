"""
Single entry point for creating notifications.

Everything in BxB should create notifications through ``notify()`` (the
signal handlers in notifications/signals.py do this for you) so that
self-notification, de-duplication and delivery preferences are applied in
one place.

Delivery model
--------------
* In-app:  a ``Notification`` row (the database foundation).
* Email:   optional, sent after the transaction commits, only when
           settings.NOTIFICATIONS_EMAIL_ENABLED is True and the user
           has email turned on for that notification type.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)

T = Notification.NotificationType

# Repeating the same action (like → unlike → like) within this window does
# not create a second notification.
DEDUPE_WINDOW = timedelta(hours=24)

DEDUPE_TYPES = {
    T.LIKE,
    T.REPOST,
    T.SAVE,
    T.SHARE,
    T.FOLLOW,
    T.EVENT_REGISTRATION,
    T.EVENT_TEAM_JOIN,
    T.WORLD_JOIN,
}

# Types that email the user by default (when email delivery is enabled).
DEFAULT_EMAIL_TYPES = {
    T.HANDSHAKE_RECEIVED,
    T.HANDSHAKE_ACCEPTED,
    T.EVENT_CANCELLED,
    T.MESSAGE,
}

# Safety cap when one action notifies many people (event publish, etc.).
MAX_FANOUT = 500


def email_enabled():
    return bool(getattr(settings, "NOTIFICATIONS_EMAIL_ENABLED", False))


def get_delivery_preferences(user, notification_type):
    """Return (in_app, email) for this user and type."""
    pref = NotificationPreference.objects.filter(
        user=user,
        notification_type=notification_type,
    ).first()

    if pref is not None:
        return pref.in_app, pref.email

    return True, notification_type in DEFAULT_EMAIL_TYPES


def _generic_target(target):
    if target is None:
        return None, None
    return ContentType.objects.get_for_model(target), target.pk


def notify(
    *,
    recipient,
    actor,
    notification_type,
    message="",
    post=None,
    comment=None,
    handshake=None,
    vibe=None,
    vibe_comment=None,
    event=None,
    target=None,
    dedupe=None,
):
    """
    Create a notification (and queue an email if the user wants one).

    Returns the Notification, or None if nothing was created (self action,
    inactive recipient, preference off, or de-duplicated).
    """
    if recipient is None or actor is None:
        return None

    if recipient.pk == actor.pk:
        return None

    if not getattr(recipient, "is_active", True):
        return None

    in_app, wants_email = get_delivery_preferences(
        recipient,
        notification_type,
    )
    wants_email = wants_email and email_enabled()

    if not in_app and not wants_email:
        return None

    message = (message or "")[:255]
    content_type, object_id = _generic_target(target)

    if not in_app:
        # Email-only: nothing is stored in the inbox.
        _queue_email(recipient, actor, notification_type, message)
        return None

    lookup = {
        "recipient": recipient,
        "actor": actor,
        "notification_type": notification_type,
        "post": post,
        "comment": comment,
        "handshake": handshake,
        "vibe": vibe,
        "vibe_comment": vibe_comment,
        "event": event,
        "content_type": content_type,
        "object_id": object_id,
    }

    if dedupe is None:
        dedupe = notification_type in DEDUPE_TYPES

    if dedupe:
        since = timezone.now() - DEDUPE_WINDOW
        if Notification.objects.filter(created_at__gte=since, **lookup).exists():
            return None

    notification = Notification.objects.create(message=message, **lookup)

    if wants_email:
        _queue_email(recipient, actor, notification_type, message)

    return notification


def notify_many(*, recipients, actor, notification_type, **kwargs):
    """Notify a bounded number of recipients; returns how many were created."""
    created = 0
    for index, recipient in enumerate(recipients):
        if index >= MAX_FANOUT:
            logger.warning(
                "notify_many hit MAX_FANOUT (%s) for %s",
                MAX_FANOUT,
                notification_type,
            )
            break
        if notify(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            **kwargs,
        ):
            created += 1
    return created


def remove_notifications(*, actor_id, notification_type, recipient_id=None, **targets):
    """
    Delete notifications created by an action that was undone
    (unlike, unsave, unfollow, un-revibe). ``targets`` are FK id filters,
    e.g. post_id=3 or vibe_id=7.
    """
    queryset = Notification.objects.filter(
        actor_id=actor_id,
        notification_type=notification_type,
        **targets,
    )
    if recipient_id is not None:
        queryset = queryset.filter(recipient_id=recipient_id)
    queryset.delete()


def notify_message(*, sender, recipient, preview="", target=None):
    """
    Hook for direct messages. BxB has no messaging model yet; call this from
    the view that saves a message::

        notify_message(sender=request.user, recipient=other, target=message_obj,
                       preview=message_obj.body[:80])
    """
    text = "sent you a message."
    if preview:
        text = f"sent you a message: {preview}"
    return notify(
        recipient=recipient,
        actor=sender,
        notification_type=T.MESSAGE,
        message=text,
        target=target,
        dedupe=False,
    )


def _queue_email(recipient, actor, notification_type, message):
    if not recipient.email:
        return

    subject = f"BitsXBytes: {actor.username} {message}".strip()[:120]
    body_lines = [f"Hi {recipient.username},", "", f"@{actor.username} {message}"]

    site_url = getattr(settings, "SITE_URL", "").rstrip("/")
    if site_url:
        body_lines += ["", f"Open your notifications: {site_url}/notifications/"]

    body_lines += [
        "",
        "You can change which emails you get in your notification settings.",
    ]

    def _send():
        try:
            send_mail(
                subject,
                "\n".join(body_lines),
                getattr(settings, "DEFAULT_FROM_EMAIL", None),
                [recipient.email],
                fail_silently=True,
            )
        except Exception:  # never let email problems break a user action
            logger.exception("Could not send notification email")

    transaction.on_commit(_send)