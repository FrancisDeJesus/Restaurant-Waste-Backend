# food_menu/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    UnitType,
    Ingredient,
    FoodItem,
    FoodIngredient,
    IngredientHistory,
    MenuItem,
    MenuItemBatch,
    IngredientPurchase,
)

# ===========================================================
# ⚖️ UNIT TYPE
# ===========================================================
@admin.register(UnitType)
class UnitTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'conversion_factor', 'base_unit')
    search_fields = ('name', 'abbreviation')


# ===========================================================
# 🧂 INGREDIENT
# ===========================================================
class IngredientHistoryInline(admin.TabularInline):
    model = IngredientHistory
    extra = 0
    readonly_fields = ('change_type', 'amount', 'unit', 'note', 'timestamp')
    can_delete = False


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'unit_type', 'quantity', 'last_updated')
    list_filter = ('unit_type', 'restaurant')
    search_fields = ('name',)
    autocomplete_fields = ('restaurant', 'unit_type')
    inlines = [IngredientHistoryInline]
    readonly_fields = ('last_updated',)

    def last_updated(self, obj):
        """Show last change time from IngredientHistory."""
        latest = obj.history.order_by('-timestamp').first()
        return latest.timestamp.strftime('%Y-%m-%d %H:%M') if latest else "—"
    last_updated.short_description = "Last Updated"


# ===========================================================
# 🍽 FOOD ITEM (Recipes)
# ===========================================================
class FoodIngredientInline(admin.TabularInline):
    model = FoodIngredient
    extra = 1


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'servings', 'created_at')
    list_filter = ('category', 'restaurant')
    search_fields = ('name',)
    autocomplete_fields = ('restaurant',)
    inlines = [FoodIngredientInline]


@admin.register(FoodIngredient)
class FoodIngredientAdmin(admin.ModelAdmin):
    list_display = ('food_item', 'ingredient', 'quantity_used', 'unit_type')
    list_filter = ('food_item', 'ingredient')
    search_fields = ('food_item__name', 'ingredient__name')


# ===========================================================
# 🍴 MENU ITEM
# ===========================================================
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'created_at')
    list_filter = ('category', 'restaurant')
    search_fields = ('name',)
    autocomplete_fields = ('restaurant',)


# ===========================================================
# 🧾 MENU ITEM BATCH (Prepared Food Tracking)
# ===========================================================
@admin.register(MenuItemBatch)
class MenuItemBatchAdmin(admin.ModelAdmin):
    list_display = (
        'menu_item',
        'quantity_prepared',
        'prepared_date',
        'expiry_date',
        'is_discarded',
        'discarded_reason',
        'status_display',
    )
    list_filter = ('is_discarded', 'expiry_date', 'menu_item__restaurant')
    search_fields = ('menu_item__name',)
    date_hierarchy = 'created_at'
    autocomplete_fields = ('menu_item',)
    readonly_fields = ('discarded_at',)

    def status_display(self, obj):
        """Color-coded status display for admin panel."""
        if obj.is_discarded:
            return format_html('<span style="color:#B71C1C;">Discarded</span>')
        elif obj.is_expired():
            return format_html('<span style="color:#E65100;">Expired</span>')
        else:
            return format_html('<span style="color:#015704;">Active</span>')
    status_display.short_description = "Status"


# ===========================================================
# 🛒 INGREDIENT PURCHASE
# ===========================================================
@admin.register(IngredientPurchase)
class IngredientPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'ingredient',
        'restaurant',
        'quantity',
        'unit',
        'purchase_date',
        'expiry_date',
        'is_expired_display',
    )
    list_filter = ('restaurant', 'expiry_date')
    search_fields = ('ingredient__name',)
    autocomplete_fields = ('restaurant', 'ingredient')

    def is_expired_display(self, obj):
        """Highlight expired ingredients."""
        if obj.is_expired():
            return format_html('<span style="color:#B71C1C;">Expired</span>')
        return format_html('<span style="color:#015704;">Valid</span>')
    is_expired_display.short_description = "Status"


# ===========================================================
# 🕓 INGREDIENT HISTORY
# ===========================================================
@admin.register(IngredientHistory)
class IngredientHistoryAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'change_type', 'amount', 'unit', 'note', 'timestamp')
    list_filter = ('change_type', 'ingredient__restaurant')
    search_fields = ('ingredient__name', 'note')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
