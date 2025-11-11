# subscriptions/management/commands/seed_subscriptions.py
from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Seed default subscription plans (Basic, Eco, Premium)."

    def handle(self, *args, **options):
        plans = [
            {
                "name": "Basic",
                "description": "Perfect for small restaurants — includes limited pickups per month.",
                "plan_type": "basic",
                "price": 0.00,
                "duration_days": 30,
                "is_active": True,
            },
            {
                "name": "Eco",
                "description": "Affordable and eco-friendly plan with regular pickups and reports.",
                "plan_type": "eco",
                "price": 499.00,
                "duration_days": 30,
                "is_active": True,
            },
            {
                "name": "Premium",
                "description": "Full access plan with priority pickups, waste analytics, and rewards.",
                "plan_type": "premium",
                "price": 999.00,
                "duration_days": 30,
                "is_active": True,
            },
        ]

        for plan in plans:
            obj, created = SubscriptionPlan.objects.update_or_create(
                plan_type=plan["plan_type"], defaults=plan
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created plan: {obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"⚙️ Updated plan: {obj.name}"))

        self.stdout.write(self.style.SUCCESS("🎉 Subscription plans seeded successfully!"))
