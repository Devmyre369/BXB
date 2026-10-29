from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from handshake.models import Handshake
from users.models import User

from .forms import ProfileForm
from .models import Follow


@login_required
def my_profile(request):
    profile = request.user.profile

    return render(
        request,
        "profiles/my_profile.html",
        {
            "profile": profile,
        },
    )


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()
            return redirect("my_profile")
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        "profiles/edit_profile.html",
        {
            "form": form,
        },
    )


def public_profile(request, username):
    profile_user = get_object_or_404(
        User,
        username=username,
    )

    profile = profile_user.profile

    is_following = False

    followers_count = Follow.objects.filter(
        following=profile_user,
    ).count()

    following_count = Follow.objects.filter(
        follower=profile_user,
    ).count()

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user,
        ).exists()

    # Default handshake state.
    handshake_status = "none"
    handshake_id = ""

    # Handshake state for logged-in users.
    if (
        request.user.is_authenticated
        and request.user != profile_user
    ):
        sent_handshake = (
            Handshake.objects.filter(
                sender=request.user,
                receiver=profile_user,
            )
            .first()
        )

        received_handshake = (
            Handshake.objects.filter(
                sender=profile_user,
                receiver=request.user,
            )
            .first()
        )

        # Accepted relationship has highest priority.
        if (
            sent_handshake
            and sent_handshake.status == "accepted"
        ):
            handshake_status = "accepted"
            handshake_id = sent_handshake.id

        elif (
            received_handshake
            and received_handshake.status == "accepted"
        ):
            handshake_status = "accepted"
            handshake_id = received_handshake.id

        # Incoming pending request.
        elif (
            received_handshake
            and received_handshake.status == "pending"
        ):
            handshake_status = "pending_received"
            handshake_id = received_handshake.id

        # Outgoing pending request.
        elif (
            sent_handshake
            and sent_handshake.status == "pending"
        ):
            handshake_status = "pending_sent"
            handshake_id = sent_handshake.id

        # A rejected outgoing request can be sent again.
        elif (
            sent_handshake
            and sent_handshake.status == "rejected"
        ):
            handshake_status = "rejected"
            handshake_id = sent_handshake.id

    # Profile connection counts.
    connection_count = (
        Handshake.objects.filter(
            Q(sender=profile_user) | Q(receiver=profile_user),
            status="accepted",
        )
        .count()
    )

    handshake_count = (
        Handshake.objects.filter(
            Q(sender=profile_user) | Q(receiver=profile_user)
        )
        .count()
    )

    return render(
        request,
        "profiles/public_profile.html",
        {
            "profile": profile,
            "profile_user": profile_user,
            "handshake_status": handshake_status,
            "handshake_id": handshake_id,
            "connection_count": connection_count,
            "handshake_count": handshake_count,
            "is_following": is_following,
            "followers_count": followers_count,
            "following_count": following_count,
        },
    )


@login_required
@require_POST
def follow_user(request, username):
    target_user = get_object_or_404(
        User,
        username=username,
    )

    if request.user == target_user:
        return JsonResponse(
            {
                "success": False,
                "error": "You cannot follow yourself.",
            },
            status=400,
        )

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user,
    )

    return JsonResponse(
        {
            "success": True,
            "following": True,
            "message": (
                f"You are now following {target_user.username}."
                if created
                else f"You already follow {target_user.username}."
            ),
        }
    )


@login_required
@require_POST
def unfollow_user(request, username):
    target_user = get_object_or_404(
        User,
        username=username,
    )

    Follow.objects.filter(
        follower=request.user,
        following=target_user,
    ).delete()

    return JsonResponse(
        {
            "success": True,
            "following": False,
            "message": f"You unfollowed {target_user.username}.",
        }
    )


def followers_list(request, username):
    profile_user = get_object_or_404(
        User,
        username=username,
    )

    followers = Follow.objects.filter(
        following=profile_user,
    ).select_related("follower")

    return render(
        request,
        "profiles/followers_list.html",
        {
            "profile_user": profile_user,
            "followers": followers,
        },
    )


def following_list(request, username):
    profile_user = get_object_or_404(
        User,
        username=username,
    )

    following = Follow.objects.filter(
        follower=profile_user,
    ).select_related("following")

    return render(
        request,
        "profiles/following_list.html",
        {
            "profile_user": profile_user,
            "following": following,
        },
    )


def connections_list(request, username):
    profile_user = get_object_or_404(
        User,
        username=username,
    )

    connections = (
        User.objects.filter(
            Q(
                handshakes_received__sender=profile_user,
                handshakes_received__status="accepted",
            )
            | Q(
                handshakes_sent__receiver=profile_user,
                handshakes_sent__status="accepted",
            )
        )
        .exclude(id=profile_user.id)
        .distinct()
        .order_by("username")
    )

    return render(
        request,
        "profiles/connections_list.html",
        {
            "profile_user": profile_user,
            "connections": connections,
        },
    )


def user_posts(request, username):
    profile_user = get_object_or_404(
        User,
        username=username,
    )

    posts = profile_user.posts.all().order_by("-created_at")

    return render(
        request,
        "profiles/user_posts.html",
        {
            "profile_user": profile_user,
            "posts": posts,
        },
    )
