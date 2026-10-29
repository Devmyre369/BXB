from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import Channel, ChannelAnnouncement, ChannelMembership


class ChannelMembershipInline(admin.TabularInline):
    model = ChannelMembership
    extra = 0


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "created_by", "created_at")
    search_fields = ("name", "college", "created_by__username")
    list_filter = ("category", "is_public")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ChannelMembershipInline]


@admin.register(ChannelAnnouncement)
class ChannelAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "channel", "author", "created_at")
    search_fields = ("title", "channel__name", "author__username")