from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import DonationDrive, Donation
from .serializers import DonationDriveSerializer, DonationSerializer

class DonationDriveViewSet(viewsets.ModelViewSet):
    queryset = DonationDrive.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = DonationDriveSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class DonationViewSet(viewsets.ModelViewSet):
    serializer_class = DonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Donation.objects.filter(user=self.request.user).order_by('-donated_at')

    @action(detail=False, methods=['get'])
    def history(self, request):
        donations = Donation.objects.filter(user=request.user).order_by('-donated_at')
        serializer = self.get_serializer(donations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def donate(self, request):
        drive_id = request.data.get('drive_id')
        amount = request.data.get('amount')

        if not drive_id or not amount:
            return Response({"error": "Drive ID and amount are required"}, status=400)

        try:
            drive = DonationDrive.objects.get(id=drive_id)
        except DonationDrive.DoesNotExist:
            return Response({"error": "Donation drive not found"}, status=404)

        donation = Donation.objects.create(
            user=request.user,
            drive=drive,
            amount=amount
        )

        drive.collected_amount += float(amount)
        drive.save()

        return Response(DonationSerializer(donation).data, status=status.HTTP_201_CREATED)
