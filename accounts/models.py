# accounts/models.py
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    restaurant_name = models.CharField(max_length=100)
    position = models.CharField(max_length=50, default="Owner")
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True, help_text="Latitude of restaurant")
    longitude = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True, help_text="Longitude of restaurant")

    def __str__(self):
        return f"{self.user.username} ({self.restaurant_name})"
