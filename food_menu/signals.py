# food_menu/signals.py
from django.db import connection
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import UnitType


@receiver(post_migrate)
def create_default_unit_types(sender, **kwargs):
    """
    Automatically creates default unit types (Piece, Kilogram, etc.)
    only after the UnitType table has been created.
    """
    if sender.name != "food_menu":
        return

    # ✅ Prevent running before the table exists
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names()
        if "food_menu_unittype" not in tables:
            return

    default_units = [
        {"name": "Piece", "abbreviation": "pc"},
        {"name": "Kilogram", "abbreviation": "kg"},
        {"name": "Gram", "abbreviation": "g"},
        {"name": "Liter", "abbreviation": "L"},
        {"name": "Milliliter", "abbreviation": "mL"},
        {"name": "Dozen", "abbreviation": "dz"},
        {"name": "Pack", "abbreviation": "pk"},
        {"name": "Bottle", "abbreviation": "btl"},
        {"name": "Box", "abbreviation": "box"},
    ]

    created_any = False
    for unit in default_units:
        if not UnitType.objects.filter(name=unit["name"]).exists():
            UnitType.objects.create(**unit)
            created_any = True

    if created_any:
        print("✅ Default unit types initialized successfully!")
