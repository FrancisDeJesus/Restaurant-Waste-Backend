# food_menu/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FoodItemViewSet, IngredientViewSet, UnitTypeViewSet

router = DefaultRouter()
router.register(r'foods', FoodItemViewSet, basename='fooditem')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')
router.register(r'unit_types', UnitTypeViewSet, basename='unit-type')

urlpatterns = [
    path('', include(router.urls)),
]
