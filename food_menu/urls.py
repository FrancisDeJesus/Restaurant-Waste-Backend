# food_menu/urls.py
from rest_framework.routers import DefaultRouter
from .views import (
    FoodItemViewSet,
    IngredientViewSet,
    UnitTypeViewSet,
    MenuItemViewSet,
    MenuItemBatchViewSet,
    IngredientPurchaseViewSet,
)

# ===========================================================
# 🍽 ROUTER SETUP
# ===========================================================
router = DefaultRouter()

# 🧂 Ingredient & Unit Type
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'unit_types', UnitTypeViewSet, basename='unittype')

# 🍳 Food (recipes & menu)
router.register(r'food_items', FoodItemViewSet, basename='fooditem')
router.register(r'menu_items', MenuItemViewSet, basename='menuitem')

# 📦 Batch & Purchase tracking
router.register(r'menu_batches', MenuItemBatchViewSet, basename='menubatch')
router.register(r'ingredient_purchases', IngredientPurchaseViewSet, basename='ingredientpurchase')

# ===========================================================
# 🔗 URL Patterns
# ===========================================================
urlpatterns = router.urls
