# food_menu/admin.py
from django.contrib import admin
from .models import UnitType, Ingredient, FoodItem, FoodIngredient


@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'unit_type', 'quantity')
    list_filter = ('unit_type', 'restaurant')
    search_fields = ('name',)
    autocomplete_fields = ('restaurant', 'unit_type')


class FoodIngredientInline(admin.TabularInline):
    model = FoodIngredient
    extra = 1


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'created_at')
    list_filter = ('category', 'restaurant')
    search_fields = ('name',)
    autocomplete_fields = ('restaurant',)
    inlines = [FoodIngredientInline]


@admin.register(FoodIngredient)
class FoodIngredientAdmin(admin.ModelAdmin):
    list_display = ('food_item', 'ingredient', 'quantity_used')
    list_filter = ('food_item', 'ingredient')
    search_fields = ('food_item__name', 'ingredient__name')
