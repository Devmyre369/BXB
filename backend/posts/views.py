from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from notifications.models import Notification
from profiles.models import Follow
from vibespace.models import Vibe, VibeLike, VibeRepost
from vibespace.forms import VibeCreateForm
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
def feed(request):
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

    vibe_form = VibeCreateForm()

    if request.method == "POST":
        vibe_form = VibeCreateForm(request.POST)

        if vibe_form.is_valid():
            vibe = vibe_form.save(commit=False)
            vibe.author = request.user
            vibe.save()
            vibe_form.save_tags(vibe)
            return redirect("feed")

    return render(
        request,
        "posts/feed.html",
        {
            "feed_items": feed_items,
            "liked_vibe_ids": liked_vibe_ids,
            "reposted_vibe_ids": reposted_vibe_ids,
            "following_creator_ids": following_creator_ids,
            "vibe_form": vibe_form,
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
        return redirect("feed")

    if request.method == "POST":
        post.delete()

    return redirect("feed")


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

        # Don't notify users about their own likes.
        '''
        if post.author != request.user:

            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                notification_type=Notification.NotificationType.LIKE,
                post=post,
                message="liked your post."
            )
            '''

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

    # Notify the post author.
    # Don't notify someone about their own comment.
    '''
    if post.author != request.user:

        Notification.objects.create(
            recipient=post.author,
            actor=request.user,
            notification_type=Notification.NotificationType.COMMENT,
            post=post,
            comment=comment,
            message="commented on your post."
        )
        '''
     # The comment notification is created by notifications.signals.

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

        # Don't notify users about their own repost.
        '''
        if post.author != request.user:

            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                notification_type=Notification.NotificationType.REPOST,
                post=post,
                message="reposted your post."
            )
            '''
        is_reposted = True

        # Notifications are created by notifications.signals.

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