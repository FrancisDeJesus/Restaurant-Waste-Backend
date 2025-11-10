from rest_framework import serializers
from .models import TrashPickup

class TrashPickupSerializer(serializers.ModelSerializer):
    waste_type_display = serializers.CharField(
        source='get_waste_type_display', read_only=True
    )
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = TrashPickup
        fields = [
            'id',
            'user',
            'waste_type',
            'waste_type_display',
            'weight_kg',
            'address',
            'latitude',     # 🆕 added
            'longitude',    # 🆕 added
            'status',
            'schedule_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'user',
            'waste_type_display',
        ]

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than zero.")
        return value

    def validate_schedule_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Schedule date cannot be in the past.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
