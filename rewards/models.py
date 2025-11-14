from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# =========================================================
# 🎯 REWARD MODEL
# =========================================================
class Reward(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reward_details = models.TextField(blank=True)
    points_required = models.PositiveIntegerField(default=0)

    # ✅ Management & availability fields
    is_active = models.BooleanField(default=True)
    available_from = models.DateTimeField(default=timezone.now)
    available_until = models.DateTimeField(null=True, blank=True)

    # ✅ Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.points_required} pts)"

    # ✅ Helper: check if reward is currently available
    @property
    def is_available(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.available_until and now > self.available_until:
            return False
        return now >= self.available_from


# =========================================================
# 🪙 REWARD POINTS MODEL
# =========================================================
class RewardPoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reward_points")
    points = models.IntegerField(default=0)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.points} pts ({self.description})"


# =========================================================
# 🎁 REWARD REDEMPTION MODEL
# =========================================================
class RewardRedemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="redemptions")
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name="redemptions")
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} redeemed {self.reward.title}"

    class Meta:
        ordering = ["-redeemed_at"]


class RedeemedHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="redeemed_history")
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name="redeemed_records")
    points_used = models.IntegerField()
    date_redeemed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} redeemed {self.reward.title}"