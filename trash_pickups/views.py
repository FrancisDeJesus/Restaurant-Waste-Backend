# trash_pickups/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rewards.models import RewardPoint
from .models import TrashPickup
from .serializers import TrashPickupSerializer


class TrashPickupViewSet(viewsets.ModelViewSet):
    """
    Handles all pickup operations:
      - Restaurant or employee creates pickups
      - Drivers accept, start, and complete pickups
      - Completion automatically grants reward points to restaurant owner
    """
    serializer_class = TrashPickupSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TrashPickup.objects.all()

    # =========================================================
    # 🔍 FILTER PICKUPS BASED ON USER ROLE
    # =========================================================
    def get_queryset(self):
        user = self.request.user

        if hasattr(user, "driver_profile"):
            return TrashPickup.objects.filter(driver=user.driver_profile).order_by("-created_at")

        elif hasattr(user, "employee_profile"):
            owner_user = user.employee_profile.owner.user
            return TrashPickup.objects.filter(user=owner_user).order_by("-created_at")

        return TrashPickup.objects.filter(user=user).order_by("-created_at")

    # =========================================================
    # 🧱 CREATE PICKUP — Always link to restaurant owner
    # =========================================================
    def create(self, request, *args, **kwargs):
        user = request.user

        # ✅ Determine restaurant owner (restaurant or employee)
        if hasattr(user, "employee_profile"):
            owner_user = user.employee_profile.owner.user
        else:
            owner_user = user

        # ✅ Get profile info (address, coordinates)
        profile = getattr(user, "profile", None)
        address = getattr(profile, "address", "")
        latitude = getattr(profile, "latitude", None)
        longitude = getattr(profile, "longitude", None)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pickup = serializer.save(
            user=owner_user,
            address=address,
            latitude=latitude,
            longitude=longitude,
            status="pending",
            driver=None,
            created_at=timezone.now(),
        )

        return Response(
            {
                "message": "Pickup created successfully and is now visible to drivers.",
                "pickup": TrashPickupSerializer(pickup, context={"request": request}).data,
            },
            status=status.HTTP_201_CREATED,
        )

    # =========================================================
    # 🚚 DRIVER ACTIONS
    # =========================================================
    @action(detail=False, methods=["get"], url_path="available")
    def available_pickups(self, request):
        user = request.user
        if not hasattr(user, "driver_profile"):
            return Response({"error": "Only drivers can view available pickups."},
                            status=status.HTTP_403_FORBIDDEN)
        pickups = TrashPickup.objects.filter(status="pending", driver__isnull=True)
        return Response(TrashPickupSerializer(pickups, many=True, context={"request": request}).data)

    @action(detail=True, methods=["patch"], url_path="accept")
    def accept_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        user = request.user
        if not hasattr(user, "driver_profile"):
            return Response({"error": "Only drivers can accept pickups."},
                            status=status.HTTP_403_FORBIDDEN)
        if pickup.status != "pending":
            return Response({"error": "Pickup already taken or completed."},
                            status=status.HTTP_400_BAD_REQUEST)
        pickup.driver = user.driver_profile
        pickup.status = "accepted"
        pickup.save()
        return Response({"message": f"Pickup #{pickup.id} accepted successfully."})

    @action(detail=True, methods=["patch"], url_path="start")
    def start_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        user = request.user
        if not hasattr(user, "driver_profile") or pickup.driver != user.driver_profile:
            return Response({"error": "You are not assigned to this pickup."},
                            status=status.HTTP_403_FORBIDDEN)
        if pickup.status != "accepted":
            return Response({"error": "Pickup must be accepted before starting."},
                            status=status.HTTP_400_BAD_REQUEST)
        pickup.status = "in_progress"
        pickup.save()
        return Response({"message": f"Pickup #{pickup.id} is now In Progress."})

    # =========================================================
    # ✅ COMPLETE PICKUP → award points to restaurant owner
    # =========================================================
    @action(detail=True, methods=["patch"], url_path="complete")
    def complete_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        user = request.user

        if not hasattr(user, "driver_profile") or pickup.driver != user.driver_profile:
            return Response({"error": "You are not assigned to this pickup."},
                            status=status.HTTP_403_FORBIDDEN)

        if pickup.status == "completed":
            return Response({"error": "Pickup already completed."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 🧮 Calculate reward points
        waste_type = (pickup.waste_type or "").lower()
        weight = float(pickup.weight_kg or 0)

        multipliers = {
            "recyclable": 2.0,
            "biodegradable": 1.5,
            "food": 1.0,
            "kitchen": 1.0,
            "customer": 1.0,
        }

        multiplier = multipliers.get(waste_type, 1.0)
        base_points = int(weight * multiplier)
        bonus_points = 5 if weight > 10 else 0
        total_points = base_points + bonus_points

        # ✅ Update pickup status and award points
        pickup.status = "completed"
        pickup.completed_at = timezone.now()
        pickup.points_awarded = total_points
        pickup.save()

        # ✅ Always award points to restaurant owner
        try:
            if hasattr(pickup.user, "employee_profile"):
                owner_user = pickup.user.employee_profile.owner.user
            else:
                owner_user = pickup.user

            RewardPoint.objects.create(
                user=owner_user,
                points=total_points,
                description=f"Completed {pickup.get_waste_type_display()} pickup ({pickup.weight_kg} kg)"
            )
            print(f"✅ Created RewardPoint for {owner_user.username} → {total_points} pts")
        except Exception as e:
            print("❌ Error creating RewardPoint:", e)

        return Response(
            {
                "message": f"Pickup #{pickup.id} completed! 🎉 {total_points} points awarded.",
                "points_awarded": total_points,
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # 🔁 CANCEL / REOPEN / HISTORY / ANALYTICS
    # =========================================================
    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        if pickup.status == "completed":
            return Response({"error": "Completed pickups cannot be cancelled."},
                            status=status.HTTP_400_BAD_REQUEST)
        pickup.status = "cancelled"
        pickup.save()
        return Response({"message": f"Pickup #{pickup.id} cancelled."})

    @action(detail=True, methods=["patch"], url_path="reopen")
    def reopen_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        user = request.user
        owner_user = pickup.user
        is_owner = user == owner_user
        is_employee = hasattr(user, "employee_profile") and user.employee_profile.owner.user == owner_user

        if not (user.is_staff or is_owner or is_employee):
            return Response({"error": "Permission denied."},
                            status=status.HTTP_403_FORBIDDEN)

        if pickup.status != "cancelled":
            return Response({"error": "Only cancelled pickups can be reopened."},
                            status=status.HTTP_400_BAD_REQUEST)

        pickup.status = "pending"
        pickup.driver = None
        pickup.save()
        return Response({"message": f"Pickup #{pickup.id} reopened and available."})

    @action(detail=False, methods=["get"], url_path="history")
    def history_pickups(self, request):
        user = request.user
        if hasattr(user, "driver_profile"):
            pickups = TrashPickup.objects.filter(driver=user.driver_profile, status="completed")
        else:
            pickups = TrashPickup.objects.filter(user=user, status="completed")
        return Response(TrashPickupSerializer(pickups, many=True).data)

    @action(detail=False, methods=["get"], url_path="analytics")
    def analytics(self, request):
        user = request.user

        if hasattr(user, "driver_profile"):
            queryset = TrashPickup.objects.filter(driver=user.driver_profile, status="completed")
        elif hasattr(user, "employee_profile"):
            owner_user = user.employee_profile.owner.user
            queryset = TrashPickup.objects.filter(user=owner_user)
        else:
            queryset = TrashPickup.objects.filter(user=user)

        total_volume = queryset.aggregate(total=Sum("weight_kg"))["total"] or 0
        by_type = queryset.values("waste_type").annotate(total=Sum("weight_kg")).order_by("-total")
        by_month = (
            queryset.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Sum("weight_kg"))
            .order_by("month")
        )

        return Response({
            "total_volume": float(total_volume),
            "by_type": {i["waste_type"]: float(i["total"]) for i in by_type},
            "by_month": {i["month"].strftime("%B %Y"): float(i["total"]) for i in by_month if i["month"]},
        })
