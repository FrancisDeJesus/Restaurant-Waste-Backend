# rewards/views.py
from django.db import models
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Reward, RewardPoint, RewardRedemption
from .serializers import RewardSerializer, RewardRedemptionSerializer

class RewardViewSet(viewsets.ModelViewSet):

    queryset = Reward.objects.filter(is_active=True)
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]

    # =========================================================
    # 🎁 LIST AVAILABLE REWARDS
    # =========================================================
    def list(self, request, *args, **kwargs):
        """Show all currently available rewards"""
        now = timezone.now()
        rewards = Reward.objects.filter(
            is_active=True,
            available_from__lte=now
        ).filter(
            models.Q(available_until__isnull=True) | models.Q(available_until__gte=now)
        )
        serializer = self.get_serializer(rewards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # =========================================================
    # 💸 REDEEM A REWARD
    # =========================================================
    @action(detail=True, methods=["post"], url_path="redeem")
    def redeem_reward(self, request, pk=None):
        """Redeem a reward if the user has enough points."""
        user = request.user
        reward = get_object_or_404(Reward, pk=pk, is_active=True)

        # ✅ Compute total available points
        total_points = RewardPoint.objects.filter(user=user).aggregate(
            total=models.Sum("points")
        )["total"] or 0

        if total_points < reward.points_required:
            return Response(
                {"error": "Not enough points to redeem this reward."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Deduct points (create a negative record)
        RewardPoint.objects.create(
            user=user,
            points=-reward.points_required,
            description=f"Redeemed {reward.title}"
        )

        # ✅ Record the redemption
        redemption = RewardRedemption.objects.create(
            user=user,
            reward=reward,
        )

        return Response(
            {
                "message": f"🎉 Successfully redeemed {reward.title}!",
                "redemption": RewardRedemptionSerializer(redemption).data,
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # 🧾 REDEMPTION HISTORY
    # =========================================================
    @action(detail=False, methods=["get"], url_path="redemptions")
    def redemption_history(self, request):
        """Show all rewards redeemed by the current user."""
        redemptions = RewardRedemption.objects.filter(
            user=request.user
        ).order_by("-redeemed_at")

        serializer = RewardRedemptionSerializer(redemptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # =========================================================
    # 💰 USER POINTS SUMMARY
    # =========================================================
    @action(detail=False, methods=["get"], url_path="points")
    def user_points(self, request):
        """
        Return current user's total reward points and recent activity.
        Ensures correct aggregation even if there are multiple entries.
        """
        user = request.user
        print(f"🔎 /rewards/points/ called by: {user.id} {user.username}")

        # ✅ Fetch all reward point records for this user
        points_qs = RewardPoint.objects.filter(user=user)

        # Debug print — optional, can remove later
        print("🧾 Found reward points:", list(points_qs.values("id", "points", "description")))

        # ✅ Correct aggregation (handles negatives and None safely)
        total_points = points_qs.aggregate(total=models.Sum("points"))["total"]
        if total_points is None:
            total_points = 0

        print("💰 Aggregated total_points =", total_points)

        # ✅ Prepare recent history (up to 10 records)
        recent_points = points_qs.order_by("-created_at")[:10]
        history = [
            {
                "description": rp.description,
                "points": rp.points,
                "date": rp.created_at.strftime("%b %d, %Y"),
            }
            for rp in recent_points
        ]

        return Response(
            {
                "total_points": total_points,
                "history": history,
            },
            status=status.HTTP_200_OK,
        )
