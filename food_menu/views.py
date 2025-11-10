# food_menu/views.py
from rest_framework.decorators import action
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import FoodItem, Ingredient, UnitType, IngredientHistory
from .serializers import (
    FoodItemSerializer,
    IngredientSerializer,
    UnitTypeSerializer,
    IngredientHistorySerializer,
)
import json


# ===========================================================
# 🍽 FOOD ITEM
# ===========================================================
class FoodItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoodItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FoodItem.objects.filter(restaurant=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        print("🧾 Incoming Food Data:", request.data)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            food = serializer.save(restaurant=self.request.user)
            return Response(self.get_serializer(food).data, status=status.HTTP_201_CREATED)
        else:
            print("❌ Food validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===========================================================
# 🧂 INGREDIENT
# ===========================================================
class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ingredient.objects.filter(restaurant=self.request.user)

    def create(self, request, *args, **kwargs):
        print("🧾 Incoming Ingredient Data:", request.data)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            ingredient = serializer.save(restaurant=self.request.user)

            # ✅ Log creation
            IngredientHistory.objects.create(
                ingredient=ingredient,
                change_type='added',
                amount=ingredient.quantity,
                unit=ingredient.unit_type.abbreviation,
                note='Ingredient created and initialized in stock.'
            )

            return Response(
                self.get_serializer(ingredient).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        ingredient = self.get_object()
        old_quantity = ingredient.quantity
        serializer = self.get_serializer(ingredient, data=request.data, partial=True)

        if serializer.is_valid():
            updated_ingredient = serializer.save()
            new_quantity = updated_ingredient.quantity

            diff = new_quantity - old_quantity
            if diff != 0:
                change_type = 'added' if diff > 0 else 'deducted'
                IngredientHistory.objects.create(
                    ingredient=updated_ingredient,
                    change_type=change_type,
                    amount=abs(diff),
                    unit=updated_ingredient.unit_type.abbreviation,
                    note=f'Manual stock {"increase" if diff > 0 else "decrease"} by user.'
                )

            return Response(
                self.get_serializer(updated_ingredient).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Custom delete — logs the deletion before removing the ingredient."""
        ingredient = self.get_object()
        try:
            IngredientHistory.objects.create(
                ingredient=ingredient,
                change_type='deducted',
                amount=ingredient.quantity,
                unit=ingredient.unit_type.abbreviation,
                note='Ingredient deleted from inventory by user.'
            )
            ingredient.delete()
            return Response(
                {"detail": f"Ingredient '{ingredient.name}' deleted and logged."},
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        ingredient = self.get_object()
        history = ingredient.history.order_by('-timestamp')
        serializer = IngredientHistorySerializer(history, many=True)
        return Response(serializer.data)


# ===========================================================
# ⚖️ UNIT TYPE
# ===========================================================
class UnitTypeViewSet(viewsets.ModelViewSet):
    queryset = UnitType.objects.all().order_by('name')
    serializer_class = UnitTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
