from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.text import slugify

from .forms import ChannelCreateForm
from .models import Channel, ChannelMembership


def channel_list(request):
    channels = Channel.objects.filter(is_public=True).select_related(
        "created_by"
    )

    return render(
        request,
        "channels/channel_list.html",
        {"channels": channels},
    )


@login_required
def channel_create(request):
    if request.method == "POST":
        form = ChannelCreateForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                channel = form.save(commit=False)
                channel.created_by = request.user

                # Generate a unique URL slug.
                base_slug = slugify(channel.name) or "channel"
                slug = base_slug
                counter = 2

                while Channel.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                channel.slug = slug
                channel.save()

                # The creator automatically becomes the first admin.
                ChannelMembership.objects.create(
                    channel=channel,
                    user=request.user,
                    role=ChannelMembership.Role.ADMIN,
                )

            return redirect("channels:list")
    else:
        form = ChannelCreateForm()

    return render(
        request,
        "channels/channel_create.html",
        {"form": form},
    )