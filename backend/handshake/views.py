import logging
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from users.models import User
from notifications.models import Notification
from notifications.services import notify

from .models import Handshake


logger = logging.getLogger(__name__)


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
@require_POST
def send_handshake(request, username):
    logger.info(
        "Handshake send endpoint reached: user=%s target=%s",
        request.user.username,
        username,
    )

    try:
        receiver = get_object_or_404(User, username=username)

        if receiver == request.user:
            return json_error(
                "You cannot send a handshake to yourself."
            )

        with transaction.atomic():
            accepted = Handshake.objects.filter(
                status=Handshake.Status.ACCEPTED,
                sender=request.user,
                receiver=receiver,
            ).exists() or Handshake.objects.filter(
                status=Handshake.Status.ACCEPTED,
                sender=receiver,
                receiver=request.user,
            ).exists()

            if accepted:
                return json_error("You are already connected.")

            reverse_pending = Handshake.objects.filter(
                sender=receiver,
                receiver=request.user,
                status=Handshake.Status.PENDING,
            ).first()

            if reverse_pending:
                return json_error(
                    "This user has already sent you a handshake. "
                    "Accept or decline their request.",
                    handshake_id=reverse_pending.id,
                    status_value=reverse_pending.status,
                )

            existing = Handshake.objects.filter(
                sender=request.user,
                receiver=receiver,
            ).first()

            if (
                existing
                and existing.status == Handshake.Status.PENDING
            ):
                return json_error(
                    "Your handshake request is already pending.",
                    handshake_id=existing.id,
                    status_value=existing.status,
                )

            if (
                existing
                and existing.status == Handshake.Status.REJECTED
            ):
                existing.status = Handshake.Status.PENDING
                existing.save(
                    update_fields=["status", "updated_at"]
                )
                handshake = existing
            else:
                handshake = Handshake.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    status=Handshake.Status.PENDING,
                )

            notify(
                recipient=receiver,
                actor=request.user,
                notification_type=(
                    Notification.NotificationType.HANDSHAKE_RECEIVED
                ),
                handshake=handshake,
                message=(
                    f"{request.user.username} sent you a handshake."
                ),
            )

        return JsonResponse({
            "success": True,
            "status": handshake.status,
            "handshake_id": handshake.id,
            "message": "Handshake request sent successfully.",
        })

    except Exception:
        logger.exception(
            "Error sending handshake: user=%s target=%s",
            request.user.username,
            username,
        )
        return json_error(
            "An internal error occurred while sending the handshake.",
            status=500,
        )


@login_required
@require_POST
def accept_handshake(request, handshake_id):
    logger.info(
        "Handshake accept endpoint reached: user=%s handshake_id=%s",
        request.user.username,
        handshake_id,
    )

    try:
        with transaction.atomic():
            handshake = get_object_or_404(
                Handshake.objects.select_for_update(),
                id=handshake_id,
            )

            if handshake.receiver != request.user:
                return json_error(
                    "You are not allowed to accept this request.",
                    status=403,
                )

            if handshake.status != Handshake.Status.PENDING:
                return json_error(
                    "This handshake is no longer pending.",
                    status_value=handshake.status,
                )

            already_connected = Handshake.objects.filter(
                sender=handshake.sender,
                receiver=handshake.receiver,
                status=Handshake.Status.ACCEPTED,
            ).exists() or Handshake.objects.filter(
                sender=handshake.receiver,
                receiver=handshake.sender,
                status=Handshake.Status.ACCEPTED,
            ).exists()

            if already_connected:
                return json_error("You are already connected.")

            handshake.status = Handshake.Status.ACCEPTED
            handshake.save(
                update_fields=["status", "updated_at"]
            )

            Handshake.objects.filter(
                sender=handshake.receiver,
                receiver=handshake.sender,
                status=Handshake.Status.PENDING,
            ).delete()

            notify(
                recipient=handshake.sender,
                actor=request.user,
                notification_type=(
                    Notification.NotificationType.HANDSHAKE_ACCEPTED
                ),
                handshake=handshake,
                message=(
                    f"{request.user.username} accepted your handshake."
                ),
            )

        return JsonResponse({
            "success": True,
            "status": Handshake.Status.ACCEPTED,
            "handshake_id": handshake.id,
            "message": "Handshake accepted successfully.",
            "message_url": None,
        })

    except Exception:
        logger.exception(
            "Error accepting handshake: user=%s handshake_id=%s",
            request.user.username,
            handshake_id,
        )
        return json_error(
            "An internal error occurred while accepting the handshake.",
            status=500,
        )


@login_required
@require_POST
def reject_handshake(request, handshake_id):
    logger.info(
        "Handshake reject endpoint reached: user=%s handshake_id=%s",
        request.user.username,
        handshake_id,
    )

    try:
        handshake = get_object_or_404(
            Handshake,
            id=handshake_id,
        )

        if handshake.receiver != request.user:
            return json_error(
                "You are not allowed to decline this request.",
                status=403,
            )

        if handshake.status != Handshake.Status.PENDING:
            return json_error(
                "This handshake is no longer pending.",
                status_value=handshake.status,
            )

        handshake.status = Handshake.Status.REJECTED
        handshake.save(
            update_fields=["status", "updated_at"]
        )

        return JsonResponse({
            "success": True,
            "status": handshake.status,
            "handshake_id": handshake.id,
            "message": "Handshake declined.",
        })

    except Exception:
        logger.exception(
            "Error rejecting handshake: user=%s handshake_id=%s",
            request.user.username,
            handshake_id,
        )
        return json_error(
            "An internal error occurred while declining the handshake.",
            status=500,
        )


@login_required
@require_POST
def cancel_handshake(request, handshake_id):
    logger.info(
        "Handshake cancel endpoint reached: user=%s handshake_id=%s",
        request.user.username,
        handshake_id,
    )

    try:
        handshake = get_object_or_404(
            Handshake,
            id=handshake_id,
        )

        if handshake.sender != request.user:
            return json_error(
                "You are not allowed to cancel this request.",
                status=403,
            )

        if handshake.status != Handshake.Status.PENDING:
            return json_error(
                "Only pending requests can be cancelled.",
            )

        handshake.delete()

        return JsonResponse({
            "success": True,
            "status": "cancelled",
            "message": "Handshake request cancelled.",
        })

    except Exception:
        logger.exception(
            "Error cancelling handshake: user=%s handshake_id=%s",
            request.user.username,
            handshake_id,
        )
        return json_error(
            "An internal error occurred while cancelling the handshake.",
            status=500,
        )
