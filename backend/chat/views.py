
'''

from django.contrib import messages as django_messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from handshake.models import Handshake
from users.models import User

from .models import Message


def get_accepted_handshake(user_a, user_b):
    """Return the accepted handshake between two users, if one exists."""
    return (
        Handshake.objects.filter(status=Handshake.Status.ACCEPTED)
        .filter(
            Q(sender=user_a, receiver=user_b)
            | Q(sender=user_b, receiver=user_a)
        )
        .first()
    )


@login_required
def inbox(request):
    """Show users with whom the current user has an accepted handshake."""
    handshakes = (
        Handshake.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            status=Handshake.Status.ACCEPTED,
        )
        .select_related("sender", "receiver")
        .order_by("-updated_at")
    )

    conversations = []
    seen_user_ids = set()

    for handshake in handshakes:
        other_user = (
            handshake.receiver
            if handshake.sender_id == request.user.id
            else handshake.sender
        )

        # Defensive de-duplication in case older data contains reciprocal
        # accepted records for the same pair.
        if other_user.id in seen_user_ids:
            continue
        seen_user_ids.add(other_user.id)

        last_message = (
            Message.objects.filter(handshake=handshake)
            .order_by("-created_at", "-id")
            .first()
        )
        unread_count = Message.objects.filter(
            handshake=handshake,
            recipient=request.user,
            is_read=False,
        ).count()

        conversations.append({
            "handshake": handshake,
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    return render(
        request,
        "messaging/inbox.html",
        {"conversations": conversations},
    )


@login_required
@require_http_methods(["GET", "POST"])
def conversation(request, username):
    """Display and send private messages with an accepted connection."""
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        django_messages.error(request, "You cannot message yourself.")
        return redirect("messaging:inbox")

    handshake = get_accepted_handshake(request.user, other_user)
    if handshake is None:
        django_messages.error(
            request,
            "You can message this person only after they accept your handshake.",
        )
        return redirect("public_profile", username=other_user.username)

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if not body:
            django_messages.error(request, "Message cannot be empty.")
        elif len(body) > 5000:
            django_messages.error(
                request,
                "Messages must be 5,000 characters or fewer.",
            )
        else:
            message = Message(
                handshake=handshake,
                sender=request.user,
                recipient=other_user,
                body=body,
            )
            # Validate the accepted handshake and participants before saving.
            message.full_clean()
            message.save()
            return redirect(
                "messaging:conversation",
                username=other_user.username,
            )

    Message.objects.filter(
        handshake=handshake,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    conversation_messages = (
        Message.objects.filter(handshake=handshake)
        .select_related("sender", "recipient")
        .order_by("created_at", "id")
    )

    return render(
        request,
        "messaging/conversation.html",
        {
            "other_user": other_user,
            "handshake": handshake,
            "conversation_messages": conversation_messages,
        },
    )




from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from users.models import User
from handshake.models import Handshake
from .models import Message


def get_accepted_handshake(user_a, user_b):
    """Return the accepted handshake between two users, if one exists."""
    return (
        Handshake.objects.filter(status=Handshake.Status.ACCEPTED)
        .filter(
            Q(sender=user_a, receiver=user_b)
            | Q(sender=user_b, receiver=user_a)
        )
        .first()
    )


@login_required
def inbox(request):
    """Display accepted connections and their latest messages."""
    handshakes = (
        Handshake.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            status=Handshake.Status.ACCEPTED,
        )
        .select_related("sender", "receiver")
        .order_by("-updated_at")
    )

    conversations = []
    seen_user_ids = set()

    for handshake in handshakes:
        if handshake.sender_id == request.user.id:
            other_user = handshake.receiver
        else:
            other_user = handshake.sender

        # Avoid duplicate conversations with the same person.
        if other_user.id in seen_user_ids:
            continue

        seen_user_ids.add(other_user.id)

        last_message = (
            Message.objects.filter(handshake=handshake)
            .order_by("-created_at", "-id")
            .first()
        )

        unread_count = Message.objects.filter(
            handshake=handshake,
            recipient=request.user,
            is_read=False,
        ).count()

        conversations.append({
            "handshake": handshake,
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    return render(
        request,
        "messaging/inbox.html",
        {"conversations": conversations},
    )


@login_required
@require_http_methods(["GET", "POST"])
def conversation(request, username):
    """Display a conversation and handle sending messages."""
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        django_messages.error(
            request, "You cannot message yourself."
        )
        return redirect("messaging:inbox")

    handshake = get_accepted_handshake(request.user, other_user)

    if handshake is None:
        django_messages.error(
            request,
            "You can message this person only after they accept your handshake.",
        )
        return redirect("public_profile", username=other_user.username)

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if not body:
            django_messages.error(request, "Message cannot be empty.")

        elif len(body) > 5000:
            django_messages.error(
                request,
                "Messages must be 5,000 characters or fewer.",
            )

        else:
            message = Message(
                handshake=handshake,
                sender=request.user,
                recipient=other_user,
                body=body,
            )

            # Validate participants and accepted-handshake status.
            message.full_clean()
            message.save()

            return redirect(
                "messaging:conversation",
                username=other_user.username,
            )

    # Mark messages received by the current user as read.
    Message.objects.filter(
        handshake=handshake,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    conversation_messages = (
        Message.objects.filter(handshake=handshake)
        .select_related("sender", "recipient")
        .order_by("created_at", "id")
    )

    return render(
        request,
        "messaging/conversation.html",
        {
            "other_user": other_user,
            "handshake": handshake,
            "conversation_messages": conversation_messages,
        },
    )
'''


from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from users.models import User
from handshake.models import Handshake
from .models import Message

'''
def get_accepted_handshake(user_a, user_b):
    """Return the accepted handshake between two users."""
    return (
        Handshake.objects.filter(status="accepted")
        .filter(
            Q(sender=user_a, receiver=user_b)
            | Q(sender=user_b, receiver=user_a)
        )
        .first()
    )
    '''

def get_accepted_handshake(user_a, user_b):
    """Return the accepted handshake between two users."""
    return (
        Handshake.objects.filter(status="accepted")
        .filter(
            Q(sender=user_a, receiver=user_b)
            | Q(sender=user_b, receiver=user_a)
        )
        .first()
    )

@login_required
def inbox(request):
    """Display accepted connections and their latest messages."""
    handshakes = (
    Handshake.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status="accepted",
    )
    .select_related("sender", "receiver")
    .order_by("-updated_at")
)
    conversations = []
    seen_user_ids = set()

    for handshake in handshakes:
        other_user = (
            handshake.receiver
            if handshake.sender_id == request.user.id
            else handshake.sender
        )

        if other_user.id in seen_user_ids:
            continue

        seen_user_ids.add(other_user.id)

        last_message = (
            Message.objects.filter(handshake=handshake)
            .order_by("-created_at", "-id")
            .first()
        )

        unread_count = Message.objects.filter(
            handshake=handshake,
            recipient=request.user,
            is_read=False,
        ).count()

        conversations.append({
            "handshake": handshake,
            "other_user": other_user,
            "last_message": last_message,
            "unread_count": unread_count,
        })

    return render(
        request,
        "chat/inbox.html",
        {"conversations": conversations},
    )


@login_required
@require_http_methods(["GET", "POST"])
def conversation(request, username):
    """Display a conversation and handle sending messages."""
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        django_messages.error(request, "You cannot message yourself.")
        return redirect("chat:inbox")

    handshake = get_accepted_handshake(request.user, other_user)

    if handshake is None:
        django_messages.error(
            request,
            "You can message this person only after they accept your handshake.",
        )
        return redirect("public_profile", username=other_user.username)

    if request.method == "POST":
        body = request.POST.get("body", "").strip()

        if not body:
            django_messages.error(request, "Message cannot be empty.")

        elif len(body) > 5000:
            django_messages.error(
                request,
                "Messages must be 5,000 characters or fewer.",
            )

        else:
            message = Message(
                handshake=handshake,
                sender=request.user,
                recipient=other_user,
                body=body,
            )
            message.full_clean()
            message.save()

            return redirect(
                "chat:conversation",
                username=other_user.username,
            )

    Message.objects.filter(
        handshake=handshake,
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    conversation_messages = (
        Message.objects.filter(handshake=handshake)
        .select_related("sender", "recipient")
        .order_by("created_at", "id")
    )

    return render(
        request,
        "chat/conversation.html",
        {
            "other_user": other_user,
            "handshake": handshake,
            "conversation_messages": conversation_messages,
        },
    )
