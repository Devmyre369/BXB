from django.shortcuts import render

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.text import slugify

from .forms import HubCreateForm
from .models import Hub, HubMembership


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
    hub = Hub.objects.filter(slug=slug).first()

    if hub is None:
        from django.http import Http404
        raise Http404("Hub not found")

    membership = HubMembership.objects.filter(
        hub=hub,
        user=request.user,
    ).first()

    if not hub.is_public and membership is None:
        from django.http import Http404
        raise Http404("Hub not found")

    return render(
        request,
        "bxb_hubs/hub_detail.html",
        {
            "hub": hub,
            "membership": membership,
        },
    )
