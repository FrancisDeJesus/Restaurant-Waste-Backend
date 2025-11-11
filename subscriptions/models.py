# subscriptions/models.py
from django.db import models
from django.contrib.auth.models import User


class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.plan_type})"


class Subscription(models.Model):
    PAYMENT_CHOICES = [
        ("GCash", "GCash"),
        ("Card", "Card"),
        ("Cash", "Cash"),
        ("Bank", "Bank"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default="GCash")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
