# donation_drive/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from .models import DonationDrive

@receiver(post_migrate)
def create_default_donation_drives(sender, **kwargs):
    if sender.name != "donation_drive":
        return

    drives = [
        {
            "title": "Davao Thermo Bio Tech Corp",
            "description": (
                "We are a DENR-EMB-accredited biodegradable waste management service provider "
                "holding a Transporter Registration Certificate (TRC) and a Treatment, Storage, "
                "and Disposal Certificate (TSD)."
            ),
            "waste_type": "kitchen",
        },
        {
            "title": "LimaDol",
            "description": (
                "Sustainable solution for upcycling community food waste"
            ),
            "waste_type": "customer",
        },
    ]

    for d in drives:
        if not DonationDrive.objects.filter(title=d["title"]).exists():
            DonationDrive.objects.create(
                title=d["title"],
                description=d["description"],
                waste_type=d["waste_type"],
                created_at=timezone.now(),
                is_active=True,
            )
            print(f"✅ Created default donation drive: {d['title']}")
