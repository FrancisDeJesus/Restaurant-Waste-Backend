# accounts/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import UserProfile
from drivers.models import Driver

# ============================================================
# 👤 USER PROFILE SERIALIZER — for /accounts/profile/
# ============================================================
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "username",
            "email",
            "restaurant_name",
            "position",
            "address",
            "latitude",
            "longitude",
            "role",
        ]
        read_only_fields = ["id", "user", "username", "email", "role"]

    def get_role(self, obj):
        user = obj.user
        if hasattr(user, "driver_profile"):
            return "driver"
        elif hasattr(user, "employee_profile"):
            return "employee"
        return "restaurant"

    def update(self, instance, validated_data):
        """
        Allows updating restaurant name, address, and coordinates
        without affecting linked user object.
        """
        instance.restaurant_name = validated_data.get("restaurant_name", instance.restaurant_name)
        instance.position = validated_data.get("position", instance.position)
        instance.address = validated_data.get("address", instance.address)
        instance.latitude = validated_data.get("latitude", instance.latitude)
        instance.longitude = validated_data.get("longitude", instance.longitude)
        instance.save()
        return instance


# ============================================================
# 🚚 DRIVER LOGIN (Custom JWT for Driver model)
# ============================================================
class DriverTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        # 1️⃣ Find driver by username
        try:
            driver = Driver.objects.get(username=username, is_active=True)
        except Driver.DoesNotExist:
            raise AuthenticationFailed("No active driver found with the given credentials")

        # 2️⃣ Validate password using Driver model helper
        if not driver.verify_password(password):
            raise AuthenticationFailed("Invalid driver credentials")

        # 3️⃣ Ensure linked Django User exists
        if not driver.user:
            user = User.objects.create_user(username=username, password=password, is_active=True)
            driver.user = user
            driver.save()
        else:
            user = driver.user
            if not user.check_password(password):
                user.set_password(password)
            if not user.is_active:
                user.is_active = True
            user.save()

        # 4️⃣ Generate JWT
        refresh = RefreshToken.for_user(driver.user)

        # 5️⃣ Handle full_name gracefully
        full_name = getattr(driver, "full_name", None) or getattr(driver, "name", None) or username

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "driver_id": driver.id,
            "full_name": full_name,
        }
