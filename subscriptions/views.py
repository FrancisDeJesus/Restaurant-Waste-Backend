# subscriptions/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import SubscriptionPlan, Subscription
from .serializers import SubscriptionPlanSerializer, SubscriptionSerializer


# ===========================================================
# 💳 SUBSCRIPTION PLAN VIEWSET
# ===========================================================
class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieve all active subscription plans.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.AllowAny]


# ===========================================================
# 🧾 USER SUBSCRIPTION MANAGEMENT
# ===========================================================
class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # -------------------------------------------------------
    # 🟢 GET ACTIVE SUBSCRIPTION
    # -------------------------------------------------------
    @action(detail=False, methods=["get"])
    def active(self, request):
        user = request.user
        active = Subscription.objects.filter(
            user=user, is_active=True, end_date__gte=timezone.now()
        ).first()

        if not active:
            return Response(
                {"detail": "No active subscription found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SubscriptionSerializer(active)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # -------------------------------------------------------
    # 💸 SUBSCRIBE TO A PLAN
    # -------------------------------------------------------
    @action(detail=False, methods=["post"])
    def subscribe(self, request):
        user = request.user
        plan_id = request.data.get("plan_id")
        payment_method = request.data.get("payment_method", "GCash")
        transaction_id = request.data.get("transaction_id", "")

        if not plan_id:
            return Response(
                {"error": "plan_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {"error": "Plan not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Deactivate any existing active subscriptions
        Subscription.objects.filter(user=user, is_active=True).update(is_active=False)

        # Create new subscription
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            end_date=timezone.now() + timezone.timedelta(days=plan.duration_days),
            payment_method=payment_method,
            transaction_id=transaction_id,
            is_active=True,
        )

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # -------------------------------------------------------
    # 🧩 SUBSCRIPTION HISTORY
    # -------------------------------------------------------
    @action(detail=False, methods=["get"])
    def history(self, request):
        user = request.user
        history = Subscription.objects.filter(user=user).order_by("-start_date")
        serializer = SubscriptionSerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
