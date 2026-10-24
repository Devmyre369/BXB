'''

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from users.models import User

from .models import Handshake


@login_required
def send_handshake(request, username):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    receiver = get_object_or_404(
        User,
        username=username
    )

    # -----------------------------------------------------
    # PREVENT SELF-HANDSHAKE
    # -----------------------------------------------------

    if receiver == request.user:
        return JsonResponse(
            {
                "success": False,
                "error": "You cannot send a handshake to yourself."
            },
            status=400
        )

    # -----------------------------------------------------
    # CHECK CURRENT DIRECTION
    # -----------------------------------------------------

    existing = (
        Handshake.objects
        .filter(
            sender=request.user,
            receiver=receiver
        )
        .first()
    )

    if existing:

        # Already pending.
        if existing.status == Handshake.Status.PENDING:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Handshake request already pending.",
                    "status": existing.status,
                    "handshake_id": existing.id,
                },
                status=400
            )

        # Already connected.
        if existing.status == Handshake.Status.ACCEPTED:

            return JsonResponse(
                {
                    "success": False,
                    "error": "You are already connected.",
                    "status": existing.status,
                    "handshake_id": existing.id,
                },
                status=400
            )

        # Previously rejected.
        # Allow the sender to send the request again.
        if existing.status == Handshake.Status.REJECTED:

            existing.status = Handshake.Status.PENDING

            existing.save(
                update_fields=[
                    "status",
                    "updated_at"
                ]
            )

            return JsonResponse(
                {
                    "success": True,
                    "status": Handshake.Status.PENDING,
                    "handshake_id": existing.id,
                    "message": "Handshake request sent again."
                }
            )

    # -----------------------------------------------------
    # CHECK REVERSE DIRECTION
    # -----------------------------------------------------

    reverse = (
        Handshake.objects
        .filter(
            sender=receiver,
            receiver=request.user
        )
        .first()
    )

    if reverse:

        # The other person already sent us a pending request.
        # Sending one back means accepting that request.
        if reverse.status == Handshake.Status.PENDING:

            reverse.status = Handshake.Status.ACCEPTED

            reverse.save(
                update_fields=[
                    "status",
                    "updated_at"
                ]
            )

            return JsonResponse(
                {
                    "success": True,
                    "status": Handshake.Status.ACCEPTED,
                    "handshake_id": reverse.id,
                    "message": "Handshake accepted."
                }
            )

        # Already connected.
        if reverse.status == Handshake.Status.ACCEPTED:

            return JsonResponse(
                {
                    "success": False,
                    "error": "You are already connected.",
                    "status": reverse.status,
                    "handshake_id": reverse.id,
                },
                status=400
            )

        # -------------------------------------------------
        # REVERSE REQUEST WAS REJECTED
        # -------------------------------------------------
        #
        # Do NOT automatically accept it.
        # We allow a completely new request in the
        # opposite direction.
        #

        if reverse.status == Handshake.Status.REJECTED:

            handshake = Handshake.objects.create(
                sender=request.user,
                receiver=receiver,
                status=Handshake.Status.PENDING
            )

            return JsonResponse(
                {
                    "success": True,
                    "status": Handshake.Status.PENDING,
                    "handshake_id": handshake.id,
                    "message": "New handshake request sent."
                }
            )

    # -----------------------------------------------------
    # BRAND NEW REQUEST
    # -----------------------------------------------------

    handshake = Handshake.objects.create(
        sender=request.user,
        receiver=receiver,
        status=Handshake.Status.PENDING
    )

    return JsonResponse(
        {
            "success": True,
            "status": Handshake.Status.PENDING,
            "handshake_id": handshake.id,
            "message": "Handshake request sent."
        }
    )


@login_required
def accept_handshake(request, handshake_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    handshake = get_object_or_404(
        Handshake,
        id=handshake_id
    )

    # Only the receiver can accept.
    if handshake.receiver != request.user:

        return JsonResponse(
            {
                "success": False,
                "error": "You are not allowed to accept this request."
            },
            status=403
        )

    if handshake.status != Handshake.Status.PENDING:

        return JsonResponse(
            {
                "success": False,
                "error": "This handshake is no longer pending.",
                "status": handshake.status,
            },
            status=400
        )

    handshake.status = Handshake.Status.ACCEPTED

    handshake.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "status": Handshake.Status.ACCEPTED,
            "handshake_id": handshake.id,
            "message": "Handshake accepted."
        }
    )


@login_required
def reject_handshake(request, handshake_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    handshake = get_object_or_404(
        Handshake,
        id=handshake_id
    )

    # Only the receiver can reject.
    if handshake.receiver != request.user:

        return JsonResponse(
            {
                "success": False,
                "error": "You are not allowed to reject this request."
            },
            status=403
        )

    if handshake.status != Handshake.Status.PENDING:

        return JsonResponse(
            {
                "success": False,
                "error": "This handshake is no longer pending.",
                "status": handshake.status,
            },
            status=400
        )

    handshake.status = Handshake.Status.REJECTED

    handshake.save(
        update_fields=[
            "status",
            "updated_at"
        ]
    )

    return JsonResponse(
        {
            "success": True,
            "status": Handshake.Status.REJECTED,
            "handshake_id": handshake.id,
            "message": "Handshake rejected."
        }
    )


@login_required
def cancel_handshake(request, handshake_id):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "POST request required."
            },
            status=405
        )

    handshake = get_object_or_404(
        Handshake,
        id=handshake_id
    )

    # Only the sender can cancel.
    if handshake.sender != request.user:

        return JsonResponse(
            {
                "success": False,
                "error": "You are not allowed to cancel this request."
            },
            status=403
        )

    if handshake.status != Handshake.Status.PENDING:

        return JsonResponse(
            {
                "success": False,
                "error": "Only pending requests can be cancelled.",
                "status": handshake.status,
            },
            status=400
        )

    handshake.delete()

    return JsonResponse(
        {
            "success": True,
            "status": "cancelled",
            "message": "Handshake request cancelled."
        }
    )
'''

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from users.models import User
from notifications.models import Notification
from notifications.services import notify

from .models import Handshake, HandshakeImage


def json_error(message, status=400, **extra):
    return JsonResponse(
        {
            "success": False,
            "error": message,
            **extra,
        },
        status=status,
    )

@login_required
def collaboration_submit(request, username):
    receiver = get_object_or_404(User, username=username)

    if receiver == request.user:
        return redirect("my_profile")

    accepted = Handshake.objects.filter(
        sender=request.user,
        receiver=receiver,
        status=Handshake.Status.ACCEPTED,
    ).exists() or Handshake.objects.filter(
        sender=receiver,
        receiver=request.user,
        status=Handshake.Status.ACCEPTED,
    ).exists()

    if accepted:
        return render(
            request,
            "handshake/collaboration_submit.html",
            {
                "receiver": receiver,
                "already_connected": True,
            },
        )

    pending = Handshake.objects.filter(
        sender=request.user,
        receiver=receiver,
        status=Handshake.Status.PENDING,
    ).exists()

    reverse_pending = Handshake.objects.filter(
        sender=receiver,
        receiver=request.user,
        status=Handshake.Status.PENDING,
    ).exists()

    if pending or reverse_pending:
        return render(
            request,
            "handshake/collaboration_submit.html",
            {
                "receiver": receiver,
                "request_pending": True,
                "reverse_pending": reverse_pending,
            },
        )

    return render(
        request,
        "handshake/collaboration_submit.html",
        {
            "receiver": receiver,
            "already_connected": False,
            "request_pending": False,
        },
    )


@login_required
def send_handshake(request, username):
    if request.method != "POST":
        return json_error("POST request required.", 405)

    receiver = get_object_or_404(User, username=username)

    if receiver == request.user:
        return json_error("You cannot send a handshake to yourself.")

    title = request.POST.get("title", "").strip()
    description = request.POST.get("description", "").strip()
    stage = request.POST.get("stage", "idea").strip()
    demo_video_url = request.POST.get("demo_video_url", "").strip()
    collaboration_needs = request.POST.get("collaboration_needs", "").strip()

    if not title:
        return json_error("Please enter an idea title.")

    if len(title) > 120:
        return json_error("The title must be 120 characters or fewer.")

    if not description:
        return json_error("Please describe your collaboration idea.")

    if len(description) > 500:
        return json_error("The description must be 500 characters or fewer.")

    if stage not in Handshake.Stage.values:
        return json_error("Please select a valid development stage.")

    if len(collaboration_needs) > 500:
        return json_error("Collaboration requirements must be 500 characters or fewer.")

    if len(demo_video_url) > 200:
        return json_error("The video URL is too long.")

    if demo_video_url and stage != Handshake.Stage.PRODUCT:
        return json_error("A demo video can only be added for a working product.")

    if demo_video_url:
        from django.core.exceptions import ValidationError
        from django.core.validators import URLValidator

        try:
            URLValidator()(demo_video_url)
        except ValidationError:
            return json_error("Please enter a valid video URL.")

    images = request.FILES.getlist("images")

    if len(images) > 5:
        return json_error("You can upload a maximum of 5 images.")

    allowed_types = {"image/jpeg", "image/png", "image/webp"}

    for image in images:
        if image.content_type not in allowed_types:
            return json_error("Upload JPG, PNG, or WebP images only.")

        if image.size > 5 * 1024 * 1024:
            return json_error("Each image must be 5 MB or smaller.")

    accepted = Handshake.objects.filter(
        status=Handshake.Status.ACCEPTED,
    ).filter(
        sender=request.user,
        receiver=receiver,
    ).exists() or Handshake.objects.filter(
        sender=receiver,
        receiver=request.user,
        status=Handshake.Status.ACCEPTED,
    ).exists()

    if accepted:
        return json_error("You are already connected.")

    pending = Handshake.objects.filter(
        sender=request.user,
        receiver=receiver,
        status=Handshake.Status.PENDING,
    ).first()

    if pending:
        return json_error(
            "Your collaboration request is already pending."
        )

    reverse_pending = Handshake.objects.filter(
        sender=receiver,
        receiver=request.user,
        status=Handshake.Status.PENDING,
    ).exists()

    if reverse_pending:
        return json_error(
            "This person has already sent you a request. "
            "Accept or decline their request instead."
        )

    with transaction.atomic():
        existing = Handshake.objects.filter(
            sender=request.user,
            receiver=receiver,
        ).first()

        if existing:
            if existing.status == Handshake.Status.ACCEPTED:
                return json_error("You are already connected.")

            existing.status = Handshake.Status.PENDING
            existing.title = title
            existing.description = description
            existing.stage = stage
            existing.demo_video_url = demo_video_url
            existing.collaboration_needs = collaboration_needs

            existing.save(
                update_fields=[
                    "status",
                    "title",
                    "description",
                    "stage",
                    "demo_video_url",
                    "collaboration_needs",
                    "updated_at",
                ]
            )

            existing.images.all().delete()
            handshake = existing

        else:
            handshake = Handshake.objects.create(
                sender=request.user,
                receiver=receiver,
                title=title,
                description=description,
                stage=stage,
                demo_video_url=demo_video_url,
                collaboration_needs=collaboration_needs,
                status=Handshake.Status.PENDING,
            )

        for image in images:
            HandshakeImage.objects.create(
                handshake=handshake,
                image=image,
            )

        notify(
            recipient=receiver,
            actor=request.user,
            notification_type=Notification.NotificationType.HANDSHAKE_RECEIVED,
            handshake=handshake,
            message=(
                f"{request.user.username} sent you a collaboration proposal."
            ),
        )

    return JsonResponse({
        "success": True,
        "status": handshake.status,
        "handshake_id": handshake.id,
        "message": "Collaboration proposal sent successfully.",
    })

@login_required
def accept_handshake(request, handshake_id):
    if request.method != "POST":
        return json_error("POST request required.", 405)

    with transaction.atomic():
        handshake = get_object_or_404(
            Handshake.objects.select_for_update(),
            id=handshake_id,
        )

        if handshake.receiver != request.user:
            return json_error(
                "You are not allowed to accept this request.",
                403,
            )

        if handshake.status != Handshake.Status.PENDING:
            return json_error(
                "This handshake is no longer pending.",
                status=handshake.status,
            )

        # Prevent accepting a second, reciprocal pending request
        # when an accepted connection already exists.
        already_connected = Handshake.objects.filter(
            status=Handshake.Status.ACCEPTED,
        ).filter(
            sender=handshake.sender,
            receiver=handshake.receiver,
        ).exists() or Handshake.objects.filter(
            sender=handshake.receiver,
            receiver=handshake.sender,
            status=Handshake.Status.ACCEPTED,
        ).exists()

        if already_connected:
            return json_error("You are already connected.")

        handshake.status = Handshake.Status.ACCEPTED
        handshake.save(update_fields=["status", "updated_at"])

        # A reverse pending request is no longer needed once
        # this connection has been accepted.
        Handshake.objects.filter(
            sender=handshake.receiver,
            receiver=handshake.sender,
            status=Handshake.Status.PENDING,
        ).delete()

        notify(
            recipient=handshake.sender,
            actor=request.user,
            notification_type=Notification.NotificationType.HANDSHAKE_ACCEPTED,
            handshake=handshake,
            message=(
                f"{request.user.username} accepted your collaboration request."
            ),
        )

    return JsonResponse({
        "success": True,
        "status": Handshake.Status.ACCEPTED,
        "handshake_id": handshake.id,
        "message": "Collaboration accepted! You are now connected.",
    })


@login_required
def reject_handshake(request, handshake_id):
    if request.method != "POST":
        return json_error("POST request required.", 405)

    handshake = get_object_or_404(Handshake, id=handshake_id)

    if handshake.receiver != request.user:
        return json_error(
            "You are not allowed to reject this request.",
            403,
        )

    if handshake.status != Handshake.Status.PENDING:
        return json_error(
            "This handshake is no longer pending.",
            status=handshake.status,
        )

    handshake.status = Handshake.Status.REJECTED
    handshake.save(update_fields=["status", "updated_at"])

    return JsonResponse({
        "success": True,
        "status": Handshake.Status.REJECTED,
        "handshake_id": handshake.id,
        "message": "Collaboration request declined.",
    })


@login_required
def cancel_handshake(request, handshake_id):
    if request.method != "POST":
        return json_error("POST request required.", 405)

    handshake = get_object_or_404(Handshake, id=handshake_id)

    if handshake.sender != request.user:
        return json_error(
            "You are not allowed to cancel this request.",
            403,
        )

    if handshake.status != Handshake.Status.PENDING:
        return json_error(
            "Only pending requests can be cancelled.",
            status=handshake.status,
        )

    handshake.delete()

    return JsonResponse({
        "success": True,
        "status": "cancelled",
        "message": "Collaboration request cancelled.",
    })
