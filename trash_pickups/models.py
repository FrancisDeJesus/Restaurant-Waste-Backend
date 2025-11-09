from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TrashPickup(models.Model):
    WASTE_TYPE_CHOICES = [
        ("kitchen", "Kitchen Waste"),
        ("food", "Food Waste"),
        ("customer", "Customer Waste"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trash_pickups")
    waste_type = models.CharField(max_length=50, choices=WASTE_TYPE_CHOICES)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    schedule_date = models.DateTimeField(default=timezone.now)
    address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.waste_type} ({self.status}) - {self.user.username}"
