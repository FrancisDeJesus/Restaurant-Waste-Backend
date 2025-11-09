from django.db import models
from django.utils import timezone
from trash_pickups.models import TrashPickup

class DonationDrive(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    waste_type = models.CharField(
        max_length=50,
        choices=TrashPickup.WASTE_TYPE_CHOICES,  # ✅ fixed name
        default="kitchen"
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.get_waste_type_display()})"



class Donation(models.Model):
    drive = models.ForeignKey(DonationDrive, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    donated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.drive.title} ({self.amount})"
