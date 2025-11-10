# food_menu/serializers.py
from rest_framework import serializers
from django.db import transaction
from .models import (
    FoodItem,
    Ingredient,
    FoodIngredient,
    UnitType,
    IngredientHistory,
)

# ===========================================================
# ⚖️ UNIT TYPE
# ===========================================================
class UnitTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ['id', 'name', 'abbreviation', 'conversion_factor']


# ===========================================================
# 🧂 INGREDIENT
# ===========================================================
class IngredientSerializer(serializers.ModelSerializer):
    unit_type_name = serializers.CharField(source="unit_type.name", read_only=True)
    unit_type_abbreviation = serializers.CharField(source="unit_type.abbreviation", read_only=True)

    class Meta:
        model = Ingredient
        fields = ["id", "name", "quantity", "unit_type", "unit_type_name", "unit_type_abbreviation"]


# ===========================================================
# 🕓 HISTORY
# ===========================================================
class IngredientHistorySerializer(serializers.ModelSerializer):
    change_type_display = serializers.CharField(source='get_change_type_display', read_only=True)
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)

    class Meta:
        model = IngredientHistory
        fields = [
            'id',
            'ingredient',
            'ingredient_name',
            'change_type',
            'change_type_display',
            'amount',
            'unit',
            'note',
            'timestamp',
        ]


# ===========================================================
# 🍽 FOOD INGREDIENT
# ===========================================================
class FoodIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    unit_type_name = serializers.CharField(source='unit_type.name', read_only=True)
    unit_type_abbreviation = serializers.CharField(source='unit_type.abbreviation', read_only=True)

    class Meta:
        model = FoodIngredient
        fields = [
            'id',
            'ingredient',
            'ingredient_name',
            'quantity_used',
            'unit_type',
            'unit_type_name',
            'unit_type_abbreviation',
        ]
        extra_kwargs = {
            'ingredient': {'required': False},
            'unit_type': {'required': False},
        }


# ===========================================================
# 🧾 FOOD ITEM
# ===========================================================
class FoodItemSerializer(serializers.ModelSerializer):
    food_ingredients = FoodIngredientSerializer(many=True, required=False)

    class Meta:
        model = FoodItem
        fields = [
            'id',
            'name',
            'description',
            'price',
            'category',
            'servings',
            'food_ingredients',
            'created_at',
        ]

    # ===========================================================
    # 🧮 CREATE — deduct stock & log usage
    # ===========================================================
    @transaction.atomic
    def create(self, validated_data):
        try:
            ingredients_data = validated_data.pop('food_ingredients', [])
            food_item = FoodItem.objects.create(**validated_data)

            for ingredient_data in ingredients_data:
                print("🔹 Processing:", ingredient_data)
                ingredient_id = ingredient_data['ingredient']
                qty_used = float(ingredient_data.get('quantity_used', 0))
                unit_type_id = ingredient_data.get('unit_type')

                ingredient_obj = Ingredient.objects.get(
                    id=ingredient_id if isinstance(ingredient_id, int) else ingredient_id.id
                )
                recipe_unit = (
                    unit_type_id if isinstance(unit_type_id, UnitType)
                    else UnitType.objects.get(id=unit_type_id)
                )
                inventory_unit = ingredient_obj.unit_type

                print(f"✅ Ingredient={ingredient_obj.name}, Qty={qty_used}, "
                      f"RecipeUnit={recipe_unit.name}, InventoryUnit={inventory_unit.name}")

                recipe_qty_base = qty_used * recipe_unit.conversion_factor
                inventory_qty_base = ingredient_obj.quantity * inventory_unit.conversion_factor

                if inventory_qty_base < recipe_qty_base:
                    raise serializers.ValidationError(
                        f"Not enough stock for '{ingredient_obj.name}'. "
                        f"Available: {ingredient_obj.quantity} {inventory_unit.abbreviation}, "
                        f"Required: {qty_used} {recipe_unit.abbreviation}."
                    )

                used_in_inventory_unit = recipe_qty_base / inventory_unit.conversion_factor
                ingredient_obj.quantity -= used_in_inventory_unit
                ingredient_obj.save()

                # ✅ Log usage in IngredientHistory
                IngredientHistory.objects.create(
                    ingredient=ingredient_obj,
                    change_type="used_in_recipe",
                    amount=qty_used,
                    unit=recipe_unit.abbreviation,
                    note=f"Used in recipe: {food_item.name}",
                )

                FoodIngredient.objects.create(
                    food_item=food_item,
                    ingredient=ingredient_obj,
                    quantity_used=qty_used,
                    unit_type=recipe_unit,
                )

            print("✅ Successfully created food item:", food_item.name)
            return food_item

        except Exception as e:
            import traceback
            print("🚨 ERROR DURING CREATE:", e)
            traceback.print_exc()
            raise serializers.ValidationError(str(e))

    # ===========================================================
    # 🔁 UPDATE — adjust ingredient list, stock, and log changes
    # ===========================================================
    @transaction.atomic
    def update(self, instance, validated_data):
        try:
            ingredients_data = validated_data.pop('food_ingredients', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if ingredients_data is not None:
                existing = {fi.ingredient_id: fi for fi in instance.food_ingredients.all()}
                new_ids = []

                for ing_data in ingredients_data:
                    ing_id = (
                        ing_data['ingredient'].id
                        if isinstance(ing_data['ingredient'], Ingredient)
                        else ing_data['ingredient']
                    )
                    qty_used = float(ing_data.get('quantity_used', 0))
                    unit_type_data = ing_data.get('unit_type')

                    new_ids.append(ing_id)
                    ingredient_obj = Ingredient.objects.get(id=ing_id)

                    recipe_unit = (
                        unit_type_data if isinstance(unit_type_data, UnitType)
                        else UnitType.objects.get(id=unit_type_data)
                    )
                    inventory_unit = ingredient_obj.unit_type

                    if ing_id in existing:
                        fi = existing[ing_id]
                        old_qty_base = fi.quantity_used * fi.unit_type.conversion_factor
                        new_qty_base = qty_used * recipe_unit.conversion_factor
                        diff_base = new_qty_base - old_qty_base

                        if diff_base > 0:
                            available_base = ingredient_obj.quantity * inventory_unit.conversion_factor
                            if available_base < diff_base:
                                raise serializers.ValidationError(
                                    f"Not enough stock to increase '{ingredient_obj.name}'."
                                )
                            ingredient_obj.quantity -= diff_base / inventory_unit.conversion_factor

                            # ✅ Log deduction
                            IngredientHistory.objects.create(
                                ingredient=ingredient_obj,
                                change_type="used_in_recipe",
                                amount=abs(diff_base) / recipe_unit.conversion_factor,
                                unit=recipe_unit.abbreviation,
                                note=f"Extra usage in {instance.name} update",
                            )

                        elif diff_base < 0:
                            ingredient_obj.quantity += abs(diff_base) / inventory_unit.conversion_factor

                            # ✅ Log restock adjustment
                            IngredientHistory.objects.create(
                                ingredient=ingredient_obj,
                                change_type="added",
                                amount=abs(diff_base) / recipe_unit.conversion_factor,
                                unit=recipe_unit.abbreviation,
                                note=f"Stock restored during {instance.name} update",
                            )

                        ingredient_obj.save()
                        fi.quantity_used = qty_used
                        fi.unit_type = recipe_unit
                        fi.save()

                    else:
                        # ✅ Handle new ingredient addition
                        recipe_qty_base = qty_used * recipe_unit.conversion_factor
                        inventory_qty_base = ingredient_obj.quantity * inventory_unit.conversion_factor
                        if inventory_qty_base < recipe_qty_base:
                            raise serializers.ValidationError(
                                f"Not enough stock for '{ingredient_obj.name}'."
                            )
                        ingredient_obj.quantity -= recipe_qty_base / inventory_unit.conversion_factor
                        ingredient_obj.save()

                        # ✅ Log new ingredient usage
                        IngredientHistory.objects.create(
                            ingredient=ingredient_obj,
                            change_type="used_in_recipe",
                            amount=qty_used,
                            unit=recipe_unit.abbreviation,
                            note=f"Newly added to {instance.name} recipe",
                        )

                        FoodIngredient.objects.create(
                            food_item=instance,
                            ingredient=ingredient_obj,
                            quantity_used=qty_used,
                            unit_type=recipe_unit,
                        )

                # ✅ Restore stock for removed ingredients
                for ing_id, fi in existing.items():
                    if ing_id not in new_ids:
                        ingredient_obj = Ingredient.objects.get(id=ing_id)
                        restore_base = fi.quantity_used * fi.unit_type.conversion_factor
                        ingredient_obj.quantity += restore_base / ingredient_obj.unit_type.conversion_factor
                        ingredient_obj.save()

                        # ✅ Log ingredient removal
                        IngredientHistory.objects.create(
                            ingredient=ingredient_obj,
                            change_type="added",
                            amount=fi.quantity_used,
                            unit=fi.unit_type.abbreviation,
                            note=f"Restored stock after removal from {instance.name}",
                        )

                        fi.delete()

            print("✅ Successfully updated food item:", instance.name)
            return instance

        except Exception as e:
            import traceback
            print("🚨 ERROR DURING UPDATE:", e)
            traceback.print_exc()
            raise serializers.ValidationError(str(e))
