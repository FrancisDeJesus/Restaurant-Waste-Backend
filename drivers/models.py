# drivers/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

class Driver(models.Model):
    # 🔗 One-to-one to Django auth user (can be created/synced at login)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='driver_profile'
    )

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # store hashed password (you already do)
    full_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        # keep your hashing behavior
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def verify_password(self, raw_password):
        return check_password(raw_password, self.password)
