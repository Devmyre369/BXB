"""
Signal handlers that connect BxB actions to notifications.

Existing views are not touched: whenever a like, revibe, comment, save,
follow, share, event registration, etc. is saved, the matching handler
creates the notification. Undoing an action (unlike, unsave, unfollow,
un-revibe) removes it again.
"""

from django.apps import apps
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from events.models import Event, EventRegistration, EventTeamMembership
from posts.models import Comment, Post, PostLike, PostSave, Repost
from profiles.models import Follow
from vibespace.models import VibeComment, VibeLike, VibeRepost

from .models import ContentShare, Notification
from .services import notify, notify_many, remove_notifications

T = Notification.NotificationType


def _skip(created, kwargs):
    """Ignore updates and fixture loading (raw=True)."""
    return (not created) or kwargs.get("raw", False)


# ---------------------------------------------------------------- posts

@receiver(post_save, sender=PostLike, dispatch_uid="notif_post_like")
def post_like_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.post.author,
        actor=instance.user,
        notification_type=T.LIKE,
        post=instance.post,
        message="liked your post.",
    )


@receiver(post_delete, sender=PostLike, dispatch_uid="notif_post_unlike")
def post_like_deleted(sender, instance, **kwargs):
    remove_notifications(
        actor_id=instance.user_id,
        notification_type=T.LIKE,
        post_id=instance.post_id,
    )


@receiver(post_save, sender=PostSave, dispatch_uid="notif_post_save")
def post_save_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.post.author,
        actor=instance.user,
        notification_type=T.SAVE,
        post=instance.post,
        message="saved your post.",
    )


@receiver(post_delete, sender=PostSave, dispatch_uid="notif_post_unsave")
def post_save_deleted(sender, instance, **kwargs):
    remove_notifications(
        actor_id=instance.user_id,
        notification_type=T.SAVE,
        post_id=instance.post_id,
    )


@receiver(post_save, sender=Comment, dispatch_uid="notif_post_comment")
def post_comment_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.post.author,
        actor=instance.user,
        notification_type=T.COMMENT,
        post=instance.post,
        comment=instance,
        message="commented on your post.",
    )


@receiver(post_save, sender=Repost, dispatch_uid="notif_post_repost")
def post_repost_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.original_post.author,
        actor=instance.user,
        notification_type=T.REPOST,
        post=instance.original_post,
        message="revibed your post.",
    )


@receiver(post_delete, sender=Repost, dispatch_uid="notif_post_unrepost")
def post_repost_deleted(sender, instance, **kwargs):
    remove_notifications(
        actor_id=instance.user_id,
        notification_type=T.REPOST,
        post_id=instance.original_post_id,
    )


# --------------------------------------------------------------- vibes

@receiver(post_save, sender=VibeLike, dispatch_uid="notif_vibe_like")
def vibe_like_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.vibe.author,
        actor=instance.user,
        notification_type=T.LIKE,
        vibe=instance.vibe,
        message="liked your Vibe.",
    )


@receiver(post_delete, sender=VibeLike, dispatch_uid="notif_vibe_unlike")
def vibe_like_deleted(sender, instance, **kwargs):
    remove_notifications(
        actor_id=instance.user_id,
        notification_type=T.LIKE,
        vibe_id=instance.vibe_id,
    )


@receiver(post_save, sender=VibeRepost, dispatch_uid="notif_vibe_revibe")
def vibe_revibe_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.vibe.author,
        actor=instance.user,
        notification_type=T.REPOST,
        vibe=instance.vibe,
        message="revibed your Vibe.",
    )


@receiver(post_delete, sender=VibeRepost, dispatch_uid="notif_vibe_unrevibe")
def vibe_revibe_deleted(sender, instance, **kwargs):
    remove_notifications(
        actor_id=instance.user_id,
        notification_type=T.REPOST,
        vibe_id=instance.vibe_id,
    )


@receiver(post_save, sender=VibeComment, dispatch_uid="notif_vibe_comment")
def vibe_comment_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.vibe.author,
        actor=instance.user,
        notification_type=T.COMMENT,
        vibe=instance.vibe,
        vibe_comment=instance,
        message="commented on your Vibe.",
    )


# -------------------------------------------------------------- follows

@receiver(post_save, sender=Follow, dispatch_uid="notif_follow")
def follow_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    notify(
        recipient=instance.following,
        actor=instance.follower,
        notification_type=T.FOLLOW,
        message="started following you.",
    )


@receiver(post_delete, sender=Follow, dispatch_uid="notif_unfollow")
def follow_deleted(sender, instance, **kwargs):
    remove_notifications(
        actor_id=instance.follower_id,
        recipient_id=instance.following_id,
        notification_type=T.FOLLOW,
    )


# --------------------------------------------------------------- shares

@receiver(post_save, sender=ContentShare, dispatch_uid="notif_share")
def share_created(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    if instance.post_id:
        notify(
            recipient=instance.post.author,
            actor=instance.user,
            notification_type=T.SHARE,
            post=instance.post,
            message="shared your post.",
        )
    elif instance.vibe_id:
        notify(
            recipient=instance.vibe.author,
            actor=instance.user,
            notification_type=T.SHARE,
            vibe=instance.vibe,
            message="shared your Vibe.",
        )


# --------------------------------------------------------------- events

@receiver(pre_save, sender=Event, dispatch_uid="notif_event_pre")
def remember_event_status(sender, instance, **kwargs):
    instance._previous_status = (
        Event.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
        if instance.pk
        else None
    )


@receiver(post_save, sender=Event, dispatch_uid="notif_event_post")
def event_saved(sender, instance, created, **kwargs):
    if kwargs.get("raw", False) or instance.created_by_id is None:
        return

    previous = getattr(instance, "_previous_status", None)
    status_changed = created or previous != instance.status

    if not status_changed:
        return

    organizer = instance.created_by

    # Newly published: tell the organizer's followers.
    if instance.status == Event.Status.PUBLISHED:
        followers = (
            Follow.objects.filter(following=organizer)
            .select_related("follower")
        )
        notify_many(
            recipients=(f.follower for f in followers.iterator()),
            actor=organizer,
            notification_type=T.EVENT_NEW,
            event=instance,
            message=f"published a new event: {instance.title}",
        )

    # Cancelled: tell everyone who was registered.
    elif instance.status == Event.Status.CANCELLED:
        registrations = (
            EventRegistration.objects.filter(
                event=instance,
                status=EventRegistration.Status.REGISTERED,
            )
            .select_related("user")
        )
        notify_many(
            recipients=(r.user for r in registrations.iterator()),
            actor=organizer,
            notification_type=T.EVENT_CANCELLED,
            event=instance,
            message=f"cancelled the event: {instance.title}",
        )


@receiver(pre_save, sender=EventRegistration, dispatch_uid="notif_reg_pre")
def remember_registration_status(sender, instance, **kwargs):
    instance._previous_status = (
        EventRegistration.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
        if instance.pk
        else None
    )


@receiver(post_save, sender=EventRegistration, dispatch_uid="notif_reg_post")
def registration_saved(sender, instance, created, **kwargs):
    if kwargs.get("raw", False):
        return

    registered = EventRegistration.Status.REGISTERED
    previous = getattr(instance, "_previous_status", None)

    if instance.status != registered or previous == registered:
        return

    notify(
        recipient=instance.event.created_by,
        actor=instance.user,
        notification_type=T.EVENT_REGISTRATION,
        event=instance.event,
        message=f"registered for your event: {instance.event.title}",
    )


@receiver(post_save, sender=EventTeamMembership, dispatch_uid="notif_team_join")
def team_member_joined(sender, instance, created, **kwargs):
    if _skip(created, kwargs):
        return
    team = instance.team
    notify(
        recipient=team.leader,
        actor=instance.user,
        notification_type=T.EVENT_TEAM_JOIN,
        event=team.event,
        message=f'joined your team "{team.name}".',
    )


# --------------------------------------------------- worlds (channels app)

def connect_world_signals():
    """
    "Worlds" map to the ``channels`` app (Channel / ChannelMembership /
    ChannelAnnouncement). That app is not in INSTALLED_APPS yet, so these
    handlers attach themselves only once it is.
    """
    if not apps.is_installed("channels"):
        return

    try:
        Membership = apps.get_model("channels", "ChannelMembership")
        Announcement = apps.get_model("channels", "ChannelAnnouncement")
    except LookupError:
        return

    def world_joined(sender, instance, created, **kwargs):
        if _skip(created, kwargs):
            return
        channel = instance.channel
        notify(
            recipient=channel.created_by,
            actor=instance.user,
            notification_type=T.WORLD_JOIN,
            target=channel,
            message=f'joined your World "{channel.name}".',
        )

    def world_announcement(sender, instance, created, **kwargs):
        if _skip(created, kwargs):
            return
        channel = instance.channel
        members = (
            channel.members.exclude(pk=instance.author_id)
            .filter(is_active=True)
        )
        notify_many(
            recipients=members.iterator(),
            actor=instance.author,
            notification_type=T.WORLD_ANNOUNCEMENT,
            target=channel,
            dedupe=False,
            message=f"posted in {channel.name}: {instance.title}",
        )

    post_save.connect(
        world_joined,
        sender=Membership,
        dispatch_uid="notif_world_join",
    )
    post_save.connect(
        world_announcement,
        sender=Announcement,
        dispatch_uid="notif_world_announcement",
    )