from django.contrib import admin
from .models import Reward, RewardPoint, RewardRedemption


# =========================================================
# 🎁 REWARD MANAGEMENT
# =========================================================
@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'description',
        'reward_details',
        'points_required',
        'is_active',
        'available_from',
        'available_until',
    )
    search_fields = ('title', 'description', 'reward_details')
    list_filter = ('is_active', 'points_required', 'available_from')
    ordering = ('-points_required',)


# =========================================================
# 💰 REWARD POINTS TRACKING
# =========================================================
@admin.register(RewardPoint)
class RewardPointAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'description', 'created_at')
    search_fields = ('user__username', 'description')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


# =========================================================
# 🧾 REWARD REDEMPTIONS
# =========================================================
@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'redeemed_at')
    search_fields = ('user__username', 'reward__title')
    list_filter = ('redeemed_at',)
    ordering = ('-redeemed_at',)
    date_hierarchy = 'redeemed_at'
