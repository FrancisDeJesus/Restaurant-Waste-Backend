# food_menu/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ---------------- UNIT TYPES ----------------------------------------
class UnitType(models.Model):

    name = models.CharField(max_length=50)
    abbreviation = models.CharField(max_length=10)
    base_unit = models.CharField(max_length=10, default="ml")  # or "g" for weight
    conversion_factor = models.FloatField(default=1.0)  # how many base units per 1 of this unit

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

# ---------------- INGREDIENTS ----------------------------------------
class Ingredient(models.Model):

    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.FloatField(default=0.0)
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit_type.abbreviation})"

    def quantity_in_base_unit(self):
        return self.quantity * self.unit_type.conversion_factor

    def adjust_quantity(self, amount, note=None):

        from .models import IngredientHistory
        change_type = "added" if amount > 0 else "deducted"
        self.quantity += amount
        self.save()
        IngredientHistory.objects.create(
            ingredient=self,
            change_type=change_type,
            amount=abs(amount),
            unit=self.unit_type.abbreviation,
            note=note or f"Stock {change_type} automatically."
        )

# ---------------- INGREDIENT PURCHASE ----------------------------------------
class IngredientPurchase(models.Model):
 
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="purchases")
    quantity = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20, default="kg")
    purchase_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return self.expiry_date and timezone.now().date() > self.expiry_date

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity} {self.unit}) - purchased {self.purchase_date}"

# ---------------- FOOD ITEMS ----------------------------------------
class FoodItem(models.Model):
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.FloatField(default=0.0)
    category = models.CharField(max_length=50, blank=True, null=True)
    servings = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    shelf_life_days = models.PositiveIntegerField(default=3)

    def __str__(self):
        return self.name

    @property
    def expiration_date(self):
        return self.created_at + timezone.timedelta(days=self.shelf_life_days)

    @property
    def is_spoiled(self):
        return timezone.now() > self.expiration_date

    def total_ingredient_cost(self):
        return sum(fi.quantity_used for fi in self.food_ingredients.all())

    def cost_per_serving(self):
        return self.total_ingredient_cost() / self.servings if self.servings > 0 else 0

# ---------------- FOOD INGREDIENT ----------------------------------------
class FoodIngredient(models.Model):
    
    food_item = models.ForeignKey(
        FoodItem, on_delete=models.CASCADE, related_name="food_ingredients"
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_used = models.FloatField(default=0.0)
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.food_item.name} uses {self.quantity_used} {self.unit_type.abbreviation} of {self.ingredient.name}"

    def usage_in_base_unit(self):
        return self.quantity_used * self.unit_type.conversion_factor

    def percentage_of_inventory_used(self):
        if self.ingredient.quantity <= 0:
            return 0
        return (self.usage_in_base_unit() / self.ingredient.quantity_in_base_unit()) * 100


# ---------------- INGREDIENT HISTORY ----------------------------------------=
class IngredientHistory(models.Model):
    CHANGE_CHOICES = [
        ("added", "Added"),
        ("deducted", "Deducted"),
        ("used_in_recipe", "Used in Recipe"),
    ]

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name="history"
    )
    change_type = models.CharField(max_length=20, choices=CHANGE_CHOICES)
    amount = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient.name} - {self.change_type} ({self.amount} {self.unit or ''})"


# ---------------- MENU ITEMS ----------------------------------------
class MenuItem(models.Model):
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ---------------- MENU ITEM (BATCH) ----------------------------------------
class MenuItemBatch(models.Model):

    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="batches")
    quantity_prepared = models.PositiveIntegerField(default=0)
    prepared_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)
    discarded_at = models.DateTimeField(null=True, blank=True)
    is_discarded = models.BooleanField(default=False)
    discarded_reason = models.CharField(max_length=255, blank=True)
    weight_discarded = models.FloatField(default=0.0, help_text="Estimated discarded food weight (kg)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Discarded" if self.is_discarded else ("Expired" if self.is_expired() else "Active")
        return f"{self.menu_item.name} (Batch #{self.id}) - {status}"

    def mark_as_discarded(self, reason="Expired"):
        """Mark this batch as discarded."""
        self.is_discarded = True
        self.discarded_reason = reason
        self.discarded_at = timezone.now()
        self.save()

    def is_expired(self):
        return self.expiry_date and timezone.now().date() > self.expiry_date
