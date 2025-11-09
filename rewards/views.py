# rewards/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Reward, RewardRedemption, RewardPoint
from .serializers import RewardSerializer, RewardRedemptionSerializer


class RewardViewSet(viewsets.ModelViewSet):
    queryset = Reward.objects.filter(is_active=True)
    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]


class RewardRedemptionViewSet(viewsets.ModelViewSet):
    serializer_class = RewardRedemptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RewardRedemption.objects.filter(user=self.request.user).order_by('-redeemed_at')

    # ✅ Redeem reward only if user has enough points
    @action(detail=False, methods=['post'])
    def redeem(self, request):
        reward_id = request.data.get('reward_id')
        user = request.user

        # Check if reward exists
        reward = get_object_or_404(Reward, id=reward_id)

        # Get or create user's reward points record
        points, created = RewardPoint.objects.get_or_create(user=user)

        # Check if user has enough points
        if points.points < reward.points_required:
            return Response(
                {
                    "error": f"Not enough points to redeem '{reward.title}'. "
                             f"You have {points.points}, need {reward.points_required}."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deduct points
        points.points -= reward.points_required
        points.save()

        # Create redemption record
        redemption = RewardRedemption.objects.create(
            user=user,
            reward=reward,
            status='completed'
        )

        return Response({
            "message": f"Successfully redeemed {reward.title}!",
            "remaining_points": points.points,
        }, status=status.HTTP_201_CREATED)

    # ✅ Redemption history
    @action(detail=False, methods=['get'])
    def history(self, request):
        redemptions = RewardRedemption.objects.filter(user=request.user).order_by('-redeemed_at')
        serializer = RewardRedemptionSerializer(redemptions, many=True)
        return Response(serializer.data)
