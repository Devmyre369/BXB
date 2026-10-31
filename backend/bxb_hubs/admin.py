from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Hub, HubMembership


class HubMembershipInline(admin.TabularInline):
    model = HubMembership
    extra = 0
    autocomplete_fields = ["user"]
    readonly_fields = ["joined_at"]


@admin.register(Hub)
class HubAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "institution",
        "created_by",
        "is_public",
        "created_at",
    )

    list_filter = ("category", "is_public", "created_at")
    search_fields = ("name", "description", "institution")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [HubMembershipInline]


@admin.register(HubMembership)
class HubMembershipAdmin(admin.ModelAdmin):
    list_display = ("hub", "user", "role", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("hub__name", "user__username")
    autocomplete_fields = ["hub", "user"]
    readonly_fields = ("joined_at",)
