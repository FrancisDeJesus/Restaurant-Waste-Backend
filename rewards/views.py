# rewards/views.py

from django.db import models
from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from .models import Reward, RewardPoint, RewardRedemption, RedeemedHistory
from .serializers import (
    RewardSerializer,
    RewardRedemptionSerializer,
    RedeemedHistorySerializer,
)

class RewardViewSet(viewsets.ModelViewSet):
    queryset = Reward.objects.filter(is_active=True)
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        now = timezone.now()

        rewards = Reward.objects.filter(
            is_active=True,
            available_from__lte=now
        ).filter(
            models.Q(available_until__isnull=True) |
            models.Q(available_until__gte=now)
        )

        serializer = self.get_serializer(rewards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="redeem")
    def redeem_reward(self, request, pk=None):
        user = request.user
        reward = get_object_or_404(Reward, pk=pk, is_active=True)

        total_points = RewardPoint.objects.filter(user=user).aggregate(
            total=models.Sum("points")
        )["total"] or 0

        if total_points < reward.points_required:
            return Response(
                {"error": "Not enough points to redeem this reward."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        RewardPoint.objects.create(
            user=user,
            points=-reward.points_required,
            description=f"Redeemed {reward.title}",
        )

        redemption = RewardRedemption.objects.create(
            user=user,
            reward=reward,
        )

        RedeemedHistory.objects.create(
            user=user,
            reward=reward,
            points_used=reward.points_required,
        )

        return Response(
            {
                "message": f"🎉 Successfully redeemed {reward.title}!",
                "redemption": RewardRedemptionSerializer(redemption).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="redemptions")
    def redemption_history(self, request):
        redemptions = RewardRedemption.objects.filter(
            user=request.user
        ).order_by("-redeemed_at")

        serializer = RewardRedemptionSerializer(redemptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="points")
    def user_points(self, request):
        user = request.user

        points_qs = RewardPoint.objects.filter(user=user)
        total_points = points_qs.aggregate(total=models.Sum("points"))["total"] or 0

        recent = points_qs.order_by("-created_at")[:10]
        history = [
            {
                "description": rp.description,
                "points": rp.points,
                "date": rp.created_at.strftime("%b %d, %Y"),
            }
            for rp in recent
        ]

        return Response(
            {
                "total_points": total_points,
                "history": history,
            },
            status=status.HTTP_200_OK,
        )

class RedeemedHistoryListView(ListAPIView):
    serializer_class = RedeemedHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RedeemedHistory.objects.filter(
            user=self.request.user
        ).order_by("-date_redeemed")
