# food_menu/serializers.py
from rest_framework import serializers
from django.db import transaction
from .models import (
    FoodItem,
    Ingredient,
    FoodIngredient,
    UnitType,
    IngredientHistory,
    MenuItem,
    MenuItemBatch,
    IngredientPurchase,
)

# ---------------- UNIT TYPES ----------------------------------------
class UnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ["id", "name", "abbreviation", "conversion_factor"]


# ---------------- INGREDIENTS ----------------------------------------
class IngredientSerializer(serializers.ModelSerializer):
    unit_type_name = serializers.CharField(source="unit_type.name", read_only=True)
    unit_type_abbreviation = serializers.CharField(source="unit_type.abbreviation", read_only=True)

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "quantity",
            "unit_type",
            "unit_type_name",
            "unit_type_abbreviation",
        ]

# ---------------- INGREDIENT HISTORY ----------------------------------------
class IngredientHistorySerializer(serializers.ModelSerializer):
    change_type_display = serializers.CharField(source="get_change_type_display", read_only=True)
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = IngredientHistory
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "change_type",
            "change_type_display",
            "amount",
            "unit",
            "note",
            "timestamp",
        ]

# ---------------- FOOD INGREDIENT ----------------------------------------
class FoodIngredientWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodIngredient
        fields = ["ingredient", "quantity_used", "unit_type"]

class FoodIngredientReadSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    unit_type_name = serializers.CharField(source="unit_type.name", read_only=True)
    unit_type_abbreviation = serializers.CharField(source="unit_type.abbreviation", read_only=True)

    class Meta:
        model = FoodIngredient
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "quantity_used",
            "unit_type",
            "unit_type_name",
            "unit_type_abbreviation",
        ]

# ---------------- FOOD ITEM ----------------------------------------
class FoodItemSerializer(serializers.ModelSerializer):
    food_ingredients = FoodIngredientWriteSerializer(many=True, write_only=True, required=False)
    ingredients = FoodIngredientReadSerializer(source="food_ingredients", many=True, read_only=True)
    expiration_date = serializers.SerializerMethodField()
    is_spoiled = serializers.SerializerMethodField()

    class Meta:
        model = FoodItem
        fields = [
            "id",
            "restaurant",
            "name",
            "description",
            "price",
            "category",
            "servings",
            "food_ingredients",
            "ingredients",
            "created_at",
            "shelf_life_days",
            "expiration_date",
            "is_spoiled",
        ]
        read_only_fields = ["restaurant", "created_at", "expiration_date", "is_spoiled"]

    def get_expiration_date(self, obj):
        if hasattr(obj, "expiration_date") and obj.expiration_date:
            # Convert to ISO 8601 string so Flutter can parse
            return obj.expiration_date.isoformat()
        # Optional: fallback to created_at + shelf_life_days
        if hasattr(obj, "shelf_life_days") and hasattr(obj, "created_at"):
            return (obj.created_at + timezone.timedelta(days=obj.shelf_life_days)).isoformat()
        return None

    def get_is_spoiled(self, obj):
        return obj.is_spoiled

    @transaction.atomic
    def create(self, validated_data):
        food_ingredients_data = validated_data.pop("food_ingredients", [])
        food_item = FoodItem.objects.create(**validated_data)

        for fi_data in food_ingredients_data:
            FoodIngredient.objects.create(food_item=food_item, **fi_data)

            ingredient = fi_data["ingredient"]
            qty_used = fi_data["quantity_used"]
            if ingredient.quantity >= qty_used:
                ingredient.quantity -= qty_used
                ingredient.save()
                IngredientHistory.objects.create(
                    ingredient=ingredient,
                    change_type="used_in_recipe",
                    amount=qty_used,
                    unit=ingredient.unit_type.abbreviation,
                    note=f"Used in new recipe '{food_item.name}'."
                )
        return food_item


# ---------------- MENU ITEM ----------------------------------------
class MenuItemSerializer(serializers.ModelSerializer):
    food_item_name = serializers.CharField(source="food_item.name", read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "description",
            "category",
            "food_item",
            "food_item_name",
            "created_at",
        ]


# ---------------- MENU ITEM (BATCH) ----------------------------------------
class MenuItemBatchSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = MenuItemBatch
        fields = [
            "id",
            "menu_item",
            "menu_item_name",
            "quantity_prepared",
            "prepared_date",
            "expiry_date",
            "is_discarded",
            "discarded_reason",
            "discarded_at",
            "weight_discarded",
            "created_at",
            "is_expired",
        ]
        read_only_fields = ["discarded_at", "is_expired"]

    def get_is_expired(self, obj):
        return obj.is_expired()

    def validate(self, data):
        expiry_date = data.get("expiry_date")
        prepared_date = data.get("prepared_date")
        if expiry_date and prepared_date and expiry_date < prepared_date:
            raise serializers.ValidationError("Expiry date cannot be before prepared date.")
        return data

# ---------------- INGREDIENT PURCHASE ----------------------------------------
class IngredientPurchaseSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = IngredientPurchase
        fields = [
            "id",
            "ingredient",
            "ingredient_name",
            "quantity",
            "unit",
            "purchase_date",
            "expiry_date",
            "is_expired",
            "created_at",
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()
