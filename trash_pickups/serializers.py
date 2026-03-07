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
            'estimated_weight_kg',
            'actual_weight_kg',
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Keep legacy key populated for old clients while new fields are available.
        data['weight_kg'] = str(instance.get_effective_weight_kg())
        return data

    def validate_weight_kg(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Weight must be greater than zero.")
        return value

    def validate_estimated_weight_kg(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Estimated weight must be greater than zero.")
        return value

    def validate_actual_weight_kg(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Actual weight must be greater than zero.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Backward compatibility: legacy clients still send weight_kg only.
        if attrs.get('estimated_weight_kg') is None and attrs.get('weight_kg') is not None:
            attrs['estimated_weight_kg'] = attrs['weight_kg']

        # New pickup creation should always include an estimate.
        if self.instance is None and attrs.get('estimated_weight_kg') is None:
            raise serializers.ValidationError(
                {'estimated_weight_kg': 'Estimated weight is required when creating a pickup.'}
            )

        return attrs

    def validate_schedule_date(self, value):
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("Schedule date cannot be in the past.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        # Keep legacy field aligned to avoid breaking older integrations.
        if validated_data.get('estimated_weight_kg') is not None:
            validated_data['weight_kg'] = validated_data['estimated_weight_kg']

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('estimated_weight_kg') is not None:
            validated_data['weight_kg'] = validated_data['estimated_weight_kg']
        return super().update(instance, validated_data)
