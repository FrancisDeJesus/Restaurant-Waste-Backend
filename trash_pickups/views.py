from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import TrashPickup
from .serializers import TrashPickupSerializer
from accounts.models import UserProfile  # ✅ import this

class TrashPickupViewSet(viewsets.ModelViewSet):
    serializer_class = TrashPickupSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 🔹 Filter pickups by user type
    def get_queryset(self):
        user = self.request.user

        # If the user is a driver, show only assigned pickups
        if hasattr(user, "driver_profile"):
            return TrashPickup.objects.filter(driver=user.driver_profile).order_by("-created_at")

        # If the user is an employee, show only the owner's pickups
        if hasattr(user, "employee_profile"):
            owner_user = user.employee_profile.owner.user
            return TrashPickup.objects.filter(user=owner_user).order_by("-created_at")

        # Default: show only the user's own pickups (restaurant)
        return TrashPickup.objects.filter(user=user).order_by("-created_at")

    # 🔹 Automatically attach current user + registered address
    def perform_create(self, serializer):
        user = self.request.user
        profile = getattr(user, "profile", None)
        address = profile.address if profile and profile.address else ""

        serializer.save(
            user=user,
            address=address,  # ✅ Auto-use restaurant’s registered address
            created_at=timezone.now(),
        )

    # ============================
    # 🚚 Custom Actions for Drivers
    # ============================

    # ✅ Accept a pickup (driver)
    @action(detail=True, methods=['patch'], url_path='accept')
    def accept_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        if pickup.status != "pending":
            return Response(
                {"error": "Only pending pickups can be accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pickup.status = "accepted"
        pickup.save()
        return Response(TrashPickupSerializer(pickup, context={"request": request}).data)

    # ✅ Start a pickup
    @action(detail=True, methods=['patch'], url_path='start')
    def start_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        if pickup.status != "accepted":
            return Response(
                {"error": "Only accepted pickups can be started."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pickup.status = "in_progress"
        pickup.save()
        return Response(TrashPickupSerializer(pickup, context={"request": request}).data)

    # ✅ Complete a pickup
    @action(detail=True, methods=['patch'], url_path='complete')
    def complete_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        if pickup.status not in ["in_progress", "accepted"]:
            return Response(
                {"error": "Pickup must be accepted or in progress before completing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pickup.status = "completed"
        pickup.save()
        return Response(TrashPickupSerializer(pickup, context={"request": request}).data)

    # ✅ Cancel a pickup
    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_pickup(self, request, pk=None):
        pickup = get_object_or_404(TrashPickup, pk=pk)
        if pickup.status == "completed":
            return Response(
                {"error": "Completed pickups cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pickup.status = "cancelled"
        pickup.save()
        return Response(TrashPickupSerializer(pickup, context={"request": request}).data)

    # ✅ View available pickups (for unassigned drivers)
    @action(detail=False, methods=['get'], url_path='available')
    def available_pickups(self, request):
        available = TrashPickup.objects.filter(status="pending").order_by("-created_at")
        serializer = TrashPickupSerializer(available, many=True, context={"request": request})
        return Response(serializer.data)
    
    # ✅ Add to TrashPickupViewSet
    @action(detail=False, methods=['get'], url_path='history')
    def history_pickups(self, request):
        user = request.user
        pickups = TrashPickup.objects.filter(
            user=user, status__in=["completed", "cancelled"]
        ).order_by('-updated_at')
        serializer = self.get_serializer(pickups, many=True)
        return Response(serializer.data)