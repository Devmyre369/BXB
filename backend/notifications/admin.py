from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import ContentShare, Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "actor",
        "notification_type",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "is_read")
    search_fields = ("recipient__username", "actor__username", "message")
    raw_id_fields = (
        "recipient",
        "actor",
        "post",
        "comment",
        "handshake",
        "vibe",
        "vibe_comment",
        "event",
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "in_app", "email")
    list_filter = ("notification_type", "in_app", "email")
    search_fields = ("user__username",)


@admin.register(ContentShare)
class ContentShareAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "vibe", "created_at")
    raw_id_fields = ("user", "post", "vibe")