# drivers/serializers.py
from rest_framework import serializers
from .models import Driver

# ==============================================================
# 🚚 DRIVER SERIALIZER (Read-only)
# ==============================================================
class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "id",
            "full_name",
            "username",
            "contact_number",
            "vehicle_type",
            "license_number",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


# ==============================================================
# 🧾 DRIVER WRITE SERIALIZER (For Admin use)
# ==============================================================
class DriverWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Driver
        fields = [
            "full_name",
            "username",
            "password",
            "contact_number",
            "vehicle_type",
            "license_number",
            "is_active",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        driver = Driver(**validated_data)
        if password:
            # ✅ Automatically hash password before saving
            driver.set_password(password)
        driver.save()
        return driver

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            # ✅ Rehash password if updated
            instance.set_password(password)
        instance.save()
        return instance
