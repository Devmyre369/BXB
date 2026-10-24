'''

from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import Notification


@login_required

def notification_list(request):
    notifications = (
        Notification.objects
        .filter(
            recipient=request.user,
            is_read=False,
        )
        .select_related(
            "actor",
            "post",
            "handshake",
            "comment",
        )
        .order_by("-created_at")
    )

    unread_count = notifications.count()

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        }
    )


@login_required
def unread_count(request):
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse(
        {
            "success": True,
            "unread_count": count,
        }
    )


@login_required
def mark_as_read(request, notification_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    notification = (
        Notification.objects
        .filter(
            id=notification_id,
            recipient=request.user
        )
        .first()
    )

    if not notification:
        return JsonResponse(
            {
                "success": False,
                "error": "Notification not found."
            },
            status=404
        )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    unread = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse(
        {
            "success": True,
            "unread_count": unread,
        }
    )


@login_required
def mark_all_as_read(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    updated = (
        Notification.objects
        .filter(
            recipient=request.user,
            is_read=False
        )
        .update(is_read=True)
    )

    return JsonResponse(
        {
            "success": True,
            "updated": updated,
            "unread_count": 0,
        }
    )
    '''

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from posts.models import Post
from vibespace.models import Vibe

from .models import ContentShare, Notification, NotificationPreference


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(
            recipient=request.user,
            is_read=False,
        )
        .select_related(
            "actor",
            "actor__profile",
            "post",
            "handshake",
            "comment",
            "vibe",
            "vibe_comment",
            "event",
        )
        .order_by("-created_at")
    )

    unread_count = notifications.count()

    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications,
            "unread_count": unread_count,
        }
    )


@login_required
def unread_count(request):
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse(
        {
            "success": True,
            "unread_count": count,
        }
    )


@login_required
def mark_as_read(request, notification_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    notification = (
        Notification.objects
        .filter(
            id=notification_id,
            recipient=request.user
        )
        .first()
    )

    if not notification:
        return JsonResponse(
            {
                "success": False,
                "error": "Notification not found."
            },
            status=404
        )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    unread = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse(
        {
            "success": True,
            "unread_count": unread,
        }
    )


@login_required
def mark_all_as_read(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    updated = (
        Notification.objects
        .filter(
            recipient=request.user,
            is_read=False
        )
        .update(is_read=True)
    )

    return JsonResponse(
        {
            "success": True,
            "updated": updated,
            "unread_count": 0,
        }
    )


# ----------------------------------------------------------------------
# SHARES
# ----------------------------------------------------------------------

# Clicking Share repeatedly should not spam the author.
SHARE_COOLDOWN = timedelta(hours=1)


def _record_share(request, **target):
    recent = ContentShare.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - SHARE_COOLDOWN,
        **target,
    ).exists()

    if not recent:
        ContentShare.objects.create(user=request.user, **target)


@login_required
@require_POST
def record_post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    _record_share(request, post=post)

    return JsonResponse(
        {
            "success": True,
            "share_count": post.shares.count(),
        }
    )


@login_required
@require_POST
def record_vibe_share(request, pk):
    vibe = get_object_or_404(Vibe, pk=pk, is_public=True)
    _record_share(request, vibe=vibe)

    return JsonResponse(
        {
            "success": True,
            "share_count": vibe.shares.count(),
        }
    )


# ----------------------------------------------------------------------
# PREFERENCES
# ----------------------------------------------------------------------

@login_required
def notification_preferences(request):
    from .services import DEFAULT_EMAIL_TYPES, email_enabled

    types = Notification.NotificationType.choices

    if request.method == "POST":
        for value, _label in types:
            NotificationPreference.objects.update_or_create(
                user=request.user,
                notification_type=value,
                defaults={
                    "in_app": f"in_app_{value}" in request.POST,
                    "email": f"email_{value}" in request.POST,
                },
            )

        return redirect("notification_preferences")

    saved = {
        pref.notification_type: pref
        for pref in NotificationPreference.objects.filter(user=request.user)
    }

    rows = []
    for value, label in types:
        pref = saved.get(value)
        rows.append(
            {
                "value": value,
                "label": label,
                "in_app": pref.in_app if pref else True,
                "email": (
                    pref.email if pref else value in DEFAULT_EMAIL_TYPES
                ),
            }
        )

    return render(
        request,
        "notifications/preferences.html",
        {
            "rows": rows,
            "email_enabled": email_enabled(),
        },
    )