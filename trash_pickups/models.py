from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from drivers.models import Driver


class TrashPickup(models.Model):
    # =========================================================
    # ♻️ CHOICES
    # =========================================================
    WASTE_TYPE_CHOICES = [
        ("kitchen", "Kitchen Waste"),
        ("food", "Food Waste"),
        ("customer", "Customer Waste"),
        ("recyclable", "Recyclable Waste"),
        ("biodegradable", "Biodegradable Waste"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    segregation_score = models.FloatField(default=0.0)


    # =========================================================
    # 👤 RELATIONSHIPS
    # =========================================================
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="trash_pickups"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="pickups"
    )

    # =========================================================
    # 🗑️ PICKUP DETAILS
    # =========================================================
    waste_type = models.CharField(max_length=50, choices=WASTE_TYPE_CHOICES)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    schedule_date = models.DateTimeField(default=timezone.now)
    address = models.CharField(max_length=255)

    # 📍 Location for map visualization
    latitude = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Pickup latitude coordinate",
    )
    longitude = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Pickup longitude coordinate",
    )

    # =========================================================
    # ⚙️ STATUS + TIMESTAMPS
    # =========================================================
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ When completed by driver (used for analytics + reward logic)
    completed_at = models.DateTimeField(null=True, blank=True)

    # =========================================================
    # 💰 (Optional) Store points earned for reference
    # =========================================================
    points_awarded = models.IntegerField(
        default=0,
        help_text="Reward points earned when completed (for reference only)",
    )

    def __str__(self):
        return f"{self.get_waste_type_display()} - {self.user.username} ({self.status})"

    class Meta:
        ordering = ["-created_at"]
