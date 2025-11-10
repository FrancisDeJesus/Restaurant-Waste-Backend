# food_menu/models.py
from django.db import models
from django.contrib.auth.models import User

# ===========================================================
# ⚖️ UNIT TYPE
# ===========================================================
class UnitType(models.Model):
    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)
    base_unit = models.CharField(max_length=10, default="ml")  # e.g., ml or g
    conversion_factor = models.FloatField(default=1.0)  # how many base units per 1 of this unit

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


# ===========================================================
# 🧂 INGREDIENT
# ===========================================================
class Ingredient(models.Model):
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.FloatField(default=0.0)
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit_type.abbreviation})"

    # ✅ Helper — Convert quantity to base unit
    def quantity_in_base_unit(self):
        return self.quantity * self.unit_type.conversion_factor


# ===========================================================
# 🍽 FOOD ITEM
# ===========================================================
class FoodItem(models.Model):
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField(default=0.0)
    category = models.CharField(max_length=50, blank=True, null=True)
    servings = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ===========================================================
# 🍱 FOOD INGREDIENT
# ===========================================================
class FoodIngredient(models.Model):
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name="food_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_used = models.FloatField(default=0.0)
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)

    def usage_in_base_unit(self):
        """Convert usage to base unit (g or ml)."""
        return self.quantity_used * self.unit_type.conversion_factor

    def percentage_of_inventory_used(self):
        """Compute how much of the ingredient stock this recipe consumes."""
        if self.ingredient.quantity <= 0:
            return 0
        used_base = self.usage_in_base_unit()
        total_base = self.ingredient.quantity_in_base_unit()
        return (used_base / total_base) * 100

    def __str__(self):
        return f"{self.food_item.name} uses {self.quantity_used} {self.unit_type.abbreviation} of {self.ingredient.name}"


# ===========================================================
# 🕓 INGREDIENT HISTORY
# ===========================================================
class IngredientHistory(models.Model):
    CHANGE_CHOICES = [
        ('added', 'Added'),
        ('deducted', 'Deducted'),
        ('used_in_recipe', 'Used in Recipe'),
    ]

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='history'
    )
    change_type = models.CharField(max_length=20, choices=CHANGE_CHOICES)
    amount = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20, blank=True, null=True)  # ✅ added safe defaults
    note = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient.name} - {self.change_type} ({self.amount} {self.unit or ''})"
