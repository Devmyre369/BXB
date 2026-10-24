from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from profiles.models import Follow
from vibespace.models import Vibe, VibeLike, VibeRepost
from notifications.models import Notification
from .models import (
    Comment,
    Post,
    PostLike,
    PostSave,
    Repost,
)


@login_required
@require_GET
def feed(request):
    user = request.user
    return render(
        request,
        "posts/home.html",
        {
            "profile_stats": {
                "posts": user.posts.count(),
                "followers": user.followers.count(),
                "following": user.following.count(),
            },
        },
    )


@login_required
@require_GET
def community_feed(request):
    user = request.user
    vibes = (
        Vibe.objects
        .filter(is_public=True)
        .select_related("author", "author__profile")
        .prefetch_related(
            "tags",
            "likes",
            "comments__user__profile",
            "reposts",
        )
        .order_by("-created_at")
    )
    liked_vibe_ids = set(
        VibeLike.objects.filter(
            vibe__in=vibes,
            user=request.user,
        ).values_list("vibe_id", flat=True)
    )
    reposted_vibe_ids = set(
        VibeRepost.objects.filter(
            vibe__in=vibes,
            user=request.user,
        ).values_list("vibe_id", flat=True)
    )
    following_creator_ids = set(
        Follow.objects.filter(
            follower=request.user,
            following__vibes__in=vibes,
        ).values_list("following_id", flat=True)
    )
    feed_items = [
        {"type": "vibe", "object": vibe}
        for vibe in vibes
    ]

    return render(
        request,
        "posts/feed.html",
        {
            "feed_items": feed_items,
            "liked_vibe_ids": liked_vibe_ids,
            "reposted_vibe_ids": reposted_vibe_ids,
            "following_creator_ids": following_creator_ids,
            "profile_stats": {
                "posts": user.posts.count(),
                "followers": user.followers.count(),
                "following": user.following.count(),
            },
        }
    )


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related(
            "author",
            "author__profile",
        ),
        id=post_id,
    )

    return render(
        request,
        "posts/detail.html",
        {"post": post},
    )


@login_required
def delete_post(request, post_id):

    post = get_object_or_404(
        Post,
        id=post_id
    )

    if post.author != request.user:
        return redirect("community_feed")

    if request.method == "POST":
        post.delete()

    return redirect("community_feed")


@login_required
def like_post(request, post_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    post = get_object_or_404(
        Post,
        id=post_id
    )

    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:

        like.delete()

        is_liked = False

    else:

        is_liked = True

    like_count = PostLike.objects.filter(
        post=post
    ).count()

    return JsonResponse(
        {
            "success": True,
            "is_liked": is_liked,
            "like_count": like_count,
        }
    )


@login_required
def save_post(request, post_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    post = get_object_or_404(
        Post,
        id=post_id
    )

    save, created = PostSave.objects.get_or_create(
        user=request.user,
        post=post
    )

    if not created:

        save.delete()

        is_saved = False

    else:

        is_saved = True

    save_count = PostSave.objects.filter(
        post=post
    ).count()

    return JsonResponse(
        {
            "success": True,
            "is_saved": is_saved,
            "save_count": save_count,
        }
    )


@login_required
def comment_post(request, post_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    post = get_object_or_404(
        Post,
        id=post_id
    )

    content = request.POST.get(
        "content",
        ""
    ).strip()

    if not content:

        return JsonResponse(
            {
                "success": False,
                "error": "Comment cannot be empty."
            },
            status=400
        )

    if len(content) > 1000:

        return JsonResponse(
            {
                "success": False,
                "error": "Comment is too long."
            },
            status=400
        )

    comment = Comment.objects.create(
        post=post,
        user=request.user,
        content=content
    )

    comment_count = Comment.objects.filter(
        post=post
    ).count()

    return JsonResponse(
        {
            "success": True,
            "comment_count": comment_count,
            "comment": {
                "id": comment.id,
                "content": comment.content,
                "username": comment.user.username,
                "created_at": comment.created_at.strftime(
                    "%b %d, %Y · %I:%M %p"
                ),
            }
        }
    )


@login_required
def repost_post(request, post_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    post = get_object_or_404(
        Post,
        id=post_id
    )

    repost, created = Repost.objects.get_or_create(
        user=request.user,
        original_post=post
    )

    if not created:

        repost.delete()

        is_reposted = False

    else:

        is_reposted = True

    repost_count = Repost.objects.filter(
        original_post=post
    ).count()

    return JsonResponse(
        {
            "success": True,
            "is_reposted": is_reposted,
            "repost_count": repost_count,
        }
    )