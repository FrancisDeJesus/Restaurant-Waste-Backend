from rest_framework import serializers
from .models import TrashPickup

class TrashPickupSerializer(serializers.ModelSerializer):
    waste_type_display = serializers.CharField(
        source='get_waste_type_display', read_only=True
    )
    user = serializers.ReadOnlyField(source='user.username')
    proof_photo_url = serializers.SerializerMethodField(read_only=True)

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
            'proof_photo',
            'proof_photo_url',
            'schedule_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'created_at',
            'updated_at',
            'user',
            'waste_type_display',
            'proof_photo_url',
        ]

    def get_proof_photo_url(self, obj):
        if not obj.proof_photo:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.proof_photo.url)
        return obj.proof_photo.url

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
