# food_menu/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import (
    FoodItem, Ingredient, UnitType, IngredientHistory,
    MenuItem, MenuItemBatch, IngredientPurchase
)
from .serializers import (
    FoodItemSerializer, IngredientSerializer, UnitTypeSerializer,
    IngredientHistorySerializer, MenuItemSerializer,
    MenuItemBatchSerializer, IngredientPurchaseSerializer
)
import json

# ---------------- FOOD ITEM ----------------------------------------
class FoodItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FoodItem.objects.filter(restaurant=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user)

# ---------------- MENU ITEM ----------------------------------------
class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MenuItem.objects.filter(restaurant=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user)


# ---------------- MENU ITEM (BATCH) ----------------------------------------
class MenuItemBatchViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = MenuItemBatch.objects.filter(menu_item__restaurant=self.request.user).order_by('-created_at')
        status_filter = self.request.query_params.get('status')

        if status_filter == 'expired':
            qs = [b for b in qs if b.is_expired()]
        elif status_filter == 'discarded':
            qs = qs.filter(is_discarded=True)
        elif status_filter == 'active':
            qs = qs.filter(is_discarded=False)
        return qs

    @transaction.atomic
    def perform_create(self, serializer):
        batch = serializer.save()
        menu_item = batch.menu_item
        servings = batch.quantity_prepared

        if not hasattr(menu_item, "food_item") or not menu_item.food_item:
            raise ValueError("Menu item has no linked FoodItem (recipe).")

        food_item = menu_item.food_item
        used_ingredients = []

        for fi in food_item.foodingredient_set.all():
            ingredient = fi.ingredient
            total_used = fi.quantity_used * servings

            original_qty = ingredient.quantity
            ingredient.quantity = max(0, ingredient.quantity - total_used)
            ingredient.save()

            IngredientHistory.objects.create(
                ingredient=ingredient,
                change_type='used_in_recipe',
                amount=total_used,
                unit=fi.unit_type.abbreviation,
                note=f'Used for batch of {menu_item.name} ({servings} servings)',
            )

            used_ingredients.append({
                "ingredient": ingredient.name,
                "used": total_used,
                "before": original_qty,
                "after": ingredient.quantity,
            })

        print(f"🔻 Ingredient deduction for {menu_item.name}:", json.dumps(used_ingredients, indent=2))

    @action(detail=True, methods=['patch'], url_path='discard')
    def discard_batch(self, request, pk=None):
        batch = self.get_object()
        reason = request.data.get('reason', 'Expired')
        weight = float(request.data.get('weight_discarded', 0))

        batch.mark_as_discarded(reason)
        batch.weight_discarded = weight
        batch.save()

        return Response({
            "message": f"Batch {batch.id} marked as discarded.",
            "discarded_reason": reason,
            "weight_discarded": weight,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Returns batch analytics summary."""
        qs = MenuItemBatch.objects.filter(menu_item__restaurant=request.user)
        total = qs.count()
        expired = len([b for b in qs if b.is_expired()])
        discarded = qs.filter(is_discarded=True).count()
        active = qs.filter(is_discarded=False).count()

        return Response({
            "total_batches": total,
            "expired_batches": expired,
            "discarded_batches": discarded,
            "active_batches": active,
        })

# ---------------- INGREDIENT PURCHASE ----------------------------------------
class IngredientPurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientPurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IngredientPurchase.objects.filter(restaurant=self.request.user).order_by('-purchase_date')

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user)

# ---------------- INGREDIENT ----------------------------------------
class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ingredient.objects.filter(restaurant=self.request.user)

    def perform_create(self, serializer):
        ingredient = serializer.save(restaurant=self.request.user)
        IngredientHistory.objects.create(
            ingredient=ingredient,
            change_type='added',
            amount=ingredient.quantity,
            unit=ingredient.unit_type.abbreviation,
            note='Ingredient created and initialized in stock.'
        )

    def perform_update(self, serializer):
        ingredient = self.get_object()
        old_qty = ingredient.quantity
        updated = serializer.save()
        diff = updated.quantity - old_qty

        if diff != 0:
            IngredientHistory.objects.create(
                ingredient=updated,
                change_type='added' if diff > 0 else 'deducted',
                amount=abs(diff),
                unit=updated.unit_type.abbreviation,
                note=f'Stock {"increased" if diff > 0 else "decreased"} manually.'
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        ingredient = self.get_object()
        history = ingredient.history.order_by('-timestamp')
        return Response(IngredientHistorySerializer(history, many=True).data)

# ---------------- UNIT TYPE ----------------------------------------
class UnitTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitType.objects.all().order_by('name')
    serializer_class = UnitTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
