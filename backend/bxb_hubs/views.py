
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils.text import slugify
from notifications.models import Notification
from notifications.services import notify
from django.db.models import Q
from .forms import HubCreateForm
from .models import Hub, HubMembership, HubJoinRequest

@login_required
def hub_list(request):
    hubs = (
        Hub.objects.filter(
            Q(is_public=True) |
            Q(memberships__user=request.user)
        )
        .distinct()
        .prefetch_related("memberships")
    )

    return render(
        request,
        "bxb_hubs/hub_list.html",
        {"hubs": hubs},
    )

def generate_unique_slug(name):
    base_slug = slugify(name)

    if not base_slug:
        base_slug = "hub"

    slug = base_slug
    counter = 1

    while Hub.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


@login_required
def create_hub(request):
    if request.method == "POST":
        form = HubCreateForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                hub = form.save(commit=False)
                hub.created_by = request.user
                hub.slug = generate_unique_slug(hub.name)
                hub.save()

                HubMembership.objects.create(
                    hub=hub,
                    user=request.user,
                    role=HubMembership.Role.OWNER,
                )

            return redirect("hubs:hub_detail", slug=hub.slug)

    else:
        form = HubCreateForm()

    return render(
        request,
        "bxb_hubs/create_hub.html",
        {"form": form},
    )


@login_required
def hub_detail(request, slug):
    hub = get_object_or_404(Hub, slug=slug)

    membership = HubMembership.objects.filter(
        hub=hub,
        user=request.user,
    ).first()

    if not hub.is_public and membership is None:
        from django.http import Http404
        raise Http404("Hub not found")

    is_owner = (
        membership is not None
        and membership.role == HubMembership.Role.OWNER
    )

    pending_join_requests = (
        HubJoinRequest.objects.filter(
            hub=hub,
            status=HubJoinRequest.Status.PENDING,
        ).select_related("user")
        if is_owner
        else HubJoinRequest.objects.none()
    )

    join_request = HubJoinRequest.objects.filter(
        hub=hub,
        user=request.user,
    ).first()

    return render(
        request,
        "bxb_hubs/hub_detail.html",
        {
            "hub": hub,
            "membership": membership,
            "is_owner": is_owner,
            "join_request": join_request,
            "pending_join_requests": pending_join_requests,
        },
    )


@login_required
@require_POST
def request_to_join(request, slug):
    with transaction.atomic():
        hub = get_object_or_404(
            Hub.objects.select_for_update(),
            slug=slug,
        )

        if HubMembership.objects.filter(
            hub=hub,
            user=request.user,
        ).exists():
            messages.info(request, "You are already a member of this Hub.")
            return redirect("hubs:hub_detail", slug=hub.slug)

        join_request = HubJoinRequest.objects.filter(
            hub=hub,
            user=request.user,
        ).first()

        if (
            join_request is not None
            and join_request.status == HubJoinRequest.Status.PENDING
        ):
            messages.info(
                request,
                "Your join request is already pending.",
            )
            return redirect("hubs:hub_detail", slug=hub.slug)

        if join_request is None:
            join_request = HubJoinRequest.objects.create(
                hub=hub,
                user=request.user,
                status=HubJoinRequest.Status.PENDING,
            )
        else:
            join_request.status = HubJoinRequest.Status.PENDING
            join_request.reviewed_by = None
            join_request.reviewed_at = None
            join_request.requested_at = timezone.now()

            join_request.save(
                update_fields=[
                    "status",
                    "reviewed_by",
                    "reviewed_at",
                    "requested_at",
                    "updated_at",
                ]
            )

    owners = HubMembership.objects.filter(
        hub=hub,
        role=HubMembership.Role.OWNER,
    ).select_related("user")

    for owner_membership in owners:
        notify(
            recipient=owner_membership.user,
            actor=request.user,
            notification_type=(
                Notification.NotificationType.HUB_JOIN_REQUEST
            ),
            message=f"requested to join {hub.name}.",
            target=hub,
            dedupe=False,
        )

    messages.success(
        request,
        "Your request to join this Hub has been sent.",
    )

    return redirect("hubs:hub_detail", slug=hub.slug)


@login_required
@require_POST
def cancel_join_request(request, slug):
    hub = get_object_or_404(Hub, slug=slug)

    join_request = HubJoinRequest.objects.filter(
        hub=hub,
        user=request.user,
        status=HubJoinRequest.Status.PENDING,
    ).first()

    if join_request is None:
        messages.error(request, "No pending join request was found.")
    else:
        join_request.status = HubJoinRequest.Status.CANCELLED
        join_request.save(update_fields=["status", "updated_at"])

        messages.success(request, "Your join request has been cancelled.")

    return redirect("hubs:hub_detail", slug=hub.slug)


@login_required
@require_POST
def accept_join_request(request, request_id):
    with transaction.atomic():
        join_request = get_object_or_404(
            HubJoinRequest.objects.select_for_update().select_related(
                "hub",
                "user",
            ),
            pk=request_id,
        )

        hub = join_request.hub

        is_owner = HubMembership.objects.filter(
            hub=hub,
            user=request.user,
            role=HubMembership.Role.OWNER,
        ).exists()

        if not is_owner:
            messages.error(
                request,
                "Only the Hub owner can review join requests.",
            )
            return redirect("hubs:hub_detail", slug=hub.slug)

        if join_request.status != HubJoinRequest.Status.PENDING:
            messages.info(
                request,
                "This join request has already been reviewed.",
            )
            return redirect("hubs:hub_detail", slug=hub.slug)

        HubMembership.objects.get_or_create(
            hub=hub,
            user=join_request.user,
            defaults={
                "role": HubMembership.Role.MEMBER,
            },
        )

        join_request.status = HubJoinRequest.Status.ACCEPTED
        join_request.reviewed_by = request.user
        join_request.reviewed_at = timezone.now()

        join_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

    notify(
        recipient=join_request.user,
        actor=request.user,
        notification_type=(
            Notification.NotificationType.HUB_JOIN_ACCEPTED
        ),
        message=f"accepted your request to join {hub.name}.",
        target=hub,
        dedupe=False,
    )

    messages.success(
        request,
        f"{join_request.user.username} has joined {hub.name}.",
    )

    return redirect("hubs:hub_detail", slug=hub.slug)


@login_required
@require_POST
def reject_join_request(request, request_id):
    with transaction.atomic():
        join_request = get_object_or_404(
            HubJoinRequest.objects.select_for_update().select_related(
                "hub",
                "user",
            ),
            pk=request_id,
        )

        hub = join_request.hub

        is_owner = HubMembership.objects.filter(
            hub=hub,
            user=request.user,
            role=HubMembership.Role.OWNER,
        ).exists()

        if not is_owner:
            messages.error(
                request,
                "Only the Hub owner can review join requests.",
            )
            return redirect("hubs:hub_detail", slug=hub.slug)

        if join_request.status != HubJoinRequest.Status.PENDING:
            messages.info(
                request,
                "This join request has already been reviewed.",
            )
            return redirect("hubs:hub_detail", slug=hub.slug)

        join_request.status = HubJoinRequest.Status.REJECTED
        join_request.reviewed_by = request.user
        join_request.reviewed_at = timezone.now()

        join_request.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "updated_at",
            ]
        )

    messages.success(request, "The join request has been rejected.")

    return redirect("hubs:hub_detail", slug=hub.slug)
