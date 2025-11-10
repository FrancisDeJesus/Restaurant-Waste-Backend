from rest_framework import serializers
from .models import DonationDrive, Donation

class DonationDriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationDrive
        fields = '__all__'


class DonationSerializer(serializers.ModelSerializer):
    drive = DonationDriveSerializer(read_only=True)
    drive_id = serializers.PrimaryKeyRelatedField(
        queryset=DonationDrive.objects.all(),
        source='drive',
        write_only=True
    )

    class Meta:
        model = Donation
        fields = [
            'id',
            'drive',
            'drive_id',
            'waste_type',
            'weight_kg',
            'donated_at',
        ]
