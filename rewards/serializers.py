from rest_framework import serializers
from .models import Reward, RewardRedemption, RewardPoint


# =========================================================
# 🎯 REWARD SERIALIZER
# =========================================================
class RewardSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()  # 👈 Computed property

    class Meta:
        model = Reward
        fields = [
            "id",
            "title",
            "description",
            "reward_details",
            "points_required",
            "is_active",
            "available_from",
            "available_until",
            "created_at",
            "updated_at",
            "is_available",
        ]
        read_only_fields = ["created_at", "updated_at", "is_available"]


# =========================================================
# 🧾 REWARD REDEMPTION SERIALIZER
# =========================================================
class RewardRedemptionSerializer(serializers.ModelSerializer):
    reward_title = serializers.CharField(source="reward.title", read_only=True)

    class Meta:
        model = RewardRedemption
        fields = ["id", "reward", "reward_title", "redeemed_at"]


# =========================================================
# 🪙 REWARD POINT SERIALIZER
# =========================================================
class RewardPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardPoint
        fields = ["id", "points", "description", "created_at"]
