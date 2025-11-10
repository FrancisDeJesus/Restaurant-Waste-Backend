from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import DonationDrive, Donation
from .serializers import DonationDriveSerializer, DonationSerializer
from trash_pickups.models import TrashPickup


class DonationDriveViewSet(viewsets.ModelViewSet):
    queryset = DonationDrive.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = DonationDriveSerializer
    permission_classes = [permissions.IsAuthenticated]

    # ✅ Optional: List only drives filtered by waste type
    @action(detail=False, methods=['get'], url_path='by-waste')
    def by_waste_type(self, request):
        waste_type = request.query_params.get('waste_type')
        if not waste_type:
            return Response(
                {"error": "Please provide a waste_type parameter (food, kitchen, customer)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        drives = DonationDrive.objects.filter(waste_type=waste_type, is_active=True)
        serializer = self.get_serializer(drives, many=True)
        return Response(serializer.data)


class DonationViewSet(viewsets.ModelViewSet):
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Show only the user's donations"""
        return Donation.objects.all().order_by('-donated_at')

    @action(detail=False, methods=['post'], url_path='donate')
    def donate(self, request):
        """
        Automatically donate based on waste type of the user's created pickup.
        Example body:
        {
            "pickup_id": 10
        }
        """
        pickup_id = request.data.get('pickup_id')
        if not pickup_id:
            return Response(
                {"error": "pickup_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pickup = get_object_or_404(TrashPickup, id=pickup_id, user=request.user)
        waste_type = pickup.waste_type

        # ✅ Automatically find corresponding donation drive by waste type
        drive = DonationDrive.objects.filter(waste_type=waste_type, is_active=True).first()
        if not drive:
            return Response(
                {"error": f"No active donation drive for waste type '{waste_type}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ✅ Create donation entry right away
        donation = Donation.objects.create(
            drive=drive,
            waste_type=waste_type,
            weight_kg=pickup.weight_kg,
            donated_at=timezone.now(),
        )

        serializer = DonationSerializer(donation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        donations = Donation.objects.all().order_by('-donated_at')
        serializer = DonationSerializer(donations, many=True)
        return Response(serializer.data)
