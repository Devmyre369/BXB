
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from profiles.models import Follow

from .forms import VibeCreateForm
from .models import Vibe, VibeComment, VibeLike


@login_required
def create_vibe(request):
    if request.method == "POST":
        form = VibeCreateForm(request.POST, request.FILES)

        if form.is_valid():
            vibe = form.save(commit=False)
            vibe.author = request.user
            vibe.save()
            form.save_tags(vibe)

            messages.success(request, "Your Vibe has been published!")
            return redirect("vibespace:detail", pk=vibe.pk)
    else:
        form = VibeCreateForm()

    return render(
        request,
        "vibespace/create.html",
        {"form": form},
    )


def explore_vibes(request):
    vibes = (
        Vibe.objects
        .filter(is_public=True)
        .select_related("author", "author__profile")
        .prefetch_related("tags")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
        )
        .order_by("-created_at")
    )

    tag_slug = request.GET.get("tag", "").strip()

    if tag_slug:
        vibes = vibes.filter(tags__slug=tag_slug)

    return render(
        request,
        "vibespace/explore.html",
        {
            "vibes": vibes,
            "selected_tag": tag_slug,
        },
    )


@login_required
def my_vibes(request):
    vibes = (
        Vibe.objects
        .filter(author=request.user)
        .select_related("author", "author__profile")
        .prefetch_related("tags")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "vibespace/my_vibes.html",
        {"vibes": vibes},
    )


@login_required
def edit_vibe(request, pk):
    vibe = get_object_or_404(Vibe, pk=pk, author=request.user)
    form = VibeCreateForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=vibe,
    )

    if request.method == "POST" and form.is_valid():
        vibe = form.save(commit=False)
        vibe.author = request.user
        vibe.save()
        form.save_tags(vibe)
        messages.success(request, "Your Vibe has been updated.")
        return redirect("vibespace:detail", pk=vibe.pk)

    return render(
        request,
        "vibespace/create.html",
        {"form": form, "vibe": vibe, "is_edit": True},
    )


@login_required
def delete_vibe(request, pk):
    vibe = get_object_or_404(Vibe, pk=pk, author=request.user)

    if request.method == "POST":
        vibe.delete()
        messages.success(request, "Your Vibe has been deleted.")
        return redirect("vibespace:my_vibes")

    return render(request, "vibespace/delete.html", {"vibe": vibe})



def vibe_detail(request, pk):
    vibe = get_object_or_404(
        Vibe.objects
        .select_related("author", "author__profile")
        .prefetch_related("tags")
        .annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", distinct=True),
        ),
        pk=pk,
    )

    # Private Vibes are visible only to their creators.
    if not vibe.is_public:
        if not request.user.is_authenticated:
            raise Http404("Vibe not found.")

        if vibe.author_id != request.user.pk:
            raise Http404("Vibe not found.")

    # Fetch comments and their authors.
    comments = (
        VibeComment.objects
        .filter(vibe=vibe)
        .select_related("user")
        .order_by("created_at")
    )

    liked = False
    is_following = False

    if request.user.is_authenticated:
        # Check whether the current user liked this Vibe.
        liked = VibeLike.objects.filter(
            vibe=vibe,
            user=request.user,
        ).exists()

        # Check whether the current user follows the creator.
        if request.user.pk != vibe.author_id:
            is_following = Follow.objects.filter(
                follower=request.user,
                following=vibe.author,
            ).exists()

    return render(
        request,
        "vibespace/detail.html",
        {
            "vibe": vibe,
            "comments": comments,
            "liked": liked,
            "is_following": is_following,
        },
    )


@login_required
@require_POST
def toggle_vibe_like(request, pk):
    vibe = get_object_or_404(
        Vibe,
        pk=pk,
        is_public=True,
    )

    existing_like = VibeLike.objects.filter(
        vibe=vibe,
        user=request.user,
    )

    if existing_like.exists():
        existing_like.delete()
        messages.success(request, "You removed your like.")
    else:
        VibeLike.objects.get_or_create(
            vibe=vibe,
            user=request.user,
        )
        messages.success(request, "You liked this Vibe.")

    return redirect("vibespace:detail", pk=pk)


@login_required
@require_POST
def add_vibe_comment(request, pk):
    vibe = get_object_or_404(
        Vibe,
        pk=pk,
        is_public=True,
    )

    text = request.POST.get("text", "").strip()

    if not text:
        messages.error(request, "Please write a comment first.")
    elif len(text) > 1000:
        messages.error(
            request,
            "Comments must be 1,000 characters or fewer.",
        )
    else:
        VibeComment.objects.create(
            vibe=vibe,
            user=request.user,
            text=text,
        )
        messages.success(request, "Comment added.")

    return redirect("vibespace:detail", pk=pk)


@login_required
@require_POST
def toggle_creator_follow(request, pk):
    vibe = get_object_or_404(
        Vibe.objects.select_related("author"),
        pk=pk,
        is_public=True,
    )

    creator = vibe.author

    if creator.pk == request.user.pk:
        messages.error(request, "You cannot follow yourself.")
        return redirect("vibespace:detail", pk=pk)

    existing_follow = Follow.objects.filter(
        follower=request.user,
        following=creator,
    )

    if existing_follow.exists():
        existing_follow.delete()
        messages.success(
            request,
            f"You unfollowed @{creator.username}.",
        )
    else:
        Follow.objects.get_or_create(
            follower=request.user,
            following=creator,
        )
        messages.success(
            request,
            f"You are now following @{creator.username}.",
        )

    return redirect("vibespace:detail", pk=pk)
