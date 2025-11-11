# subscriptions/serializers.py
from rest_framework import serializers
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "name",
            "description",
            "plan_type",
            "price",
            "duration_days",
            "is_active",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "plan_name",
            "start_date",
            "end_date",
            "is_active",
            "payment_method",
            "transaction_id",
        ]
