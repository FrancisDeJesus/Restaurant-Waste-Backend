# drivers/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Driver
from .serializers import DriverSerializer, DriverWriteSerializer
from trash_pickups.models import TrashPickup
from trash_pickups.serializers import TrashPickupSerializer


# =========================================================
# 🔒 Custom Permission: Admin or Driver Owner
# =========================================================
class IsAdminOrDriverSelf(permissions.BasePermission):
    """
    Allow access if:
    - user is staff (admin), OR
    - user is the driver linked to the object
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if hasattr(request.user, "driver_profile"):
            return obj == request.user.driver_profile
        return False


# =========================================================
# 🚚 DRIVER VIEWSET
# =========================================================
class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.filter(is_active=True)

    # ✅ Dynamic permissions
    def get_permissions(self):
        # Allow authenticated drivers for operational actions
        if self.action in [
            "me",
            "assigned_pickups",
            "available_pickups",
            "accept_pickup",
            "start",
            "complete_pickup",
            "history",
        ]:
            return [permissions.IsAuthenticated()]
        # Admin-only for CRUD operations
        return [permissions.IsAdminUser()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DriverWriteSerializer
        return DriverSerializer

    # =========================================================
    # 👤 DRIVER PROFILE (GET /drivers/me/)
    # =========================================================
    @action(detail=False, methods=["get"], url_path="me", permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Return the logged-in driver's profile."""
        if not hasattr(request.user, "driver_profile"):
            return Response(
                {"detail": "Not a driver account."},
                status=status.HTTP_403_FORBIDDEN,
            )
        driver = request.user.driver_profile
        serializer = DriverSerializer(driver, context={"request": request})
        return Response(serializer.data)

    # =========================================================
    # 🚚 VIEW ASSIGNED PICKUPS (GET /drivers/{id}/assigned/)
    # =========================================================
    @action(detail=True, methods=["get"], url_path="assigned")
    def assigned_pickups(self, request, pk=None):
        """List all active pickups assigned to this driver."""
        driver = get_object_or_404(Driver, pk=pk)

        # Permission: only this driver or admin
        if not request.user.is_staff:
            if not hasattr(request.user, "driver_profile") or request.user.driver_profile.id != driver.id:
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        pickups = TrashPickup.objects.filter(driver=driver).exclude(status="completed").order_by("-created_at")
        serializer = TrashPickupSerializer(pickups, many=True, context={"request": request})
        return Response(serializer.data)

    # =========================================================
    # 📦 AVAILABLE PICKUPS (GET /drivers/available/)
    # =========================================================
    @action(detail=False, methods=["get"], url_path="available", permission_classes=[permissions.IsAuthenticated],)

    def available_pickups(self, request):

        if not request.user.is_staff and not hasattr(request.user, "driver_profile"):
            return Response(
                {"detail": "Only drivers or admins can view available pickups."},
                status=status.HTTP_403_FORBIDDEN,
            )

        pickups = TrashPickup.objects.filter(status="pending", driver__isnull=True).order_by("-created_at")

        serializer = TrashPickupSerializer(pickups, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # =========================================================
    # 🕓 DRIVER HISTORY (GET /drivers/{id}/history/)
    # =========================================================
    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        """View all completed pickups for this driver."""
        driver = get_object_or_404(Driver, pk=pk)

        # Permission: only self or admin
        if not request.user.is_staff:
            if not hasattr(request.user, "driver_profile") or request.user.driver_profile.id != driver.id:
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        pickups = TrashPickup.objects.filter(driver=driver, status="completed").order_by("-updated_at")
        serializer = TrashPickupSerializer(pickups, many=True, context={"request": request})
        return Response(serializer.data)

    # =========================================================
    # 🧱 ACCEPT PICKUP (PATCH /drivers/{id}/accept/)
    # =========================================================
    @action(detail=True, methods=["patch"], url_path="accept")
    def accept_pickup(self, request, pk=None):
        """Driver accepts a pending pickup."""
        driver = getattr(request.user, "driver_profile", None)
        if not driver:
            return Response({"detail": "Only drivers can accept pickups."}, status=status.HTTP_403_FORBIDDEN)

        # Prevent one driver from accepting for another
        if driver.id != int(pk) and not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        pickup_id = request.data.get("pickup_id")
        if not pickup_id:
            return Response({"error": "pickup_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        pickup = get_object_or_404(TrashPickup, pk=pickup_id, status="pending", driver__isnull=True)
        pickup.driver = driver
        pickup.status = "accepted"
        pickup.save()

        return Response({"message": f"Pickup #{pickup.id} assigned to {driver.full_name}."}, status=status.HTTP_200_OK)

    # =========================================================
    # 🚀 START PICKUP (PATCH /drivers/{id}/start/)
    # =========================================================
    @action(detail=True, methods=["patch"])
    def start(self, request, pk=None):
        """Driver starts or resumes an accepted pickup."""
        driver = get_object_or_404(Driver, pk=pk)

        # ✅ Permission: only the driver or admin
        if not request.user.is_staff:
            if not hasattr(request.user, "driver_profile") or request.user.driver_profile.id != driver.id:
                return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ Allow both "accepted" and "in_progress"
        pickup = (
            TrashPickup.objects.filter(driver=driver, status__in=["accepted", "in_progress"])
            .order_by("-created_at")
            .first()
        )

        if not pickup:
            return Response(
                {"detail": "No TrashPickup matches the given query."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if pickup.status != "in_progress":
            pickup.status = "in_progress"
            pickup.save()

        serializer = TrashPickupSerializer(pickup)
        return Response(
            {"message": f"Pickup {pickup.id} started", "pickup": serializer.data},
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # ✅ COMPLETE PICKUP (PATCH /drivers/{id}/complete/)
    # =========================================================
    @action(detail=True, methods=["patch"], url_path="complete")
    def complete_pickup(self, request, pk=None):
        """Driver completes the pickup."""
        driver = getattr(request.user, "driver_profile", None)
        if not driver:
            return Response({"detail": "Only drivers can complete pickups."}, status=status.HTTP_403_FORBIDDEN)

        if driver.id != int(pk) and not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        pickup_id = request.data.get("pickup_id")
        if not pickup_id:
            return Response({"error": "pickup_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        pickup = get_object_or_404(TrashPickup, pk=pickup_id, driver=driver)
        if pickup.status not in ["accepted", "in_progress"]:
            return Response({"error": "Pickup must be accepted or in progress."}, status=status.HTTP_400_BAD_REQUEST)

        pickup.status = "completed"
        pickup.save()

        return Response({"message": f"Pickup #{pickup.id} completed successfully."}, status=status.HTTP_200_OK)
