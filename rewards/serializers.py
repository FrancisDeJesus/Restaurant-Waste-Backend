from rest_framework import serializers
from .models import Reward, RewardRedemption, RewardPoint, RedeemedHistory

# ------------ REWARDS SERIALIZER ----------------------------------------
class RewardSerializer(serializers.ModelSerializer):
    is_available = serializers.ReadOnlyField()  

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


# ------------ REWARDS REDEMPTION ----------------------------------------
class RewardRedemptionSerializer(serializers.ModelSerializer):
    reward_title = serializers.CharField(source="reward.title", read_only=True)

    class Meta:
        model = RewardRedemption
        fields = ["id", "reward", "reward_title", "redeemed_at"]


# ------------ REWARDS POINTS ----------------------------------------
class RewardPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardPoint
        fields = ["id", "points", "description", "created_at"]

# ------------ REWARDS HISTORY ----------------------------------------
class RedeemedHistorySerializer(serializers.ModelSerializer):
    reward_name = serializers.CharField(source="reward.name", read_only=True)

    class Meta:
        model = RedeemedHistory
        fields = ["id", "reward_name", "points_used", "date_redeemed"]