# rewards/admin.py
from django.contrib import admin
from .models import Reward, RewardRedemption

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("title", "points_required", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ("user", "reward", "status", "redeemed_at")
    list_filter = ("status",)
    search_fields = ("user__username", "reward__title")
