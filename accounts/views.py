# accounts/views.py
from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from .models import UserProfile


# ─────────────────────────────────────────────
# 👤 Registration Serializer
# ─────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(write_only=True)
    email = serializers.CharField(required=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'restaurant_name',
            'address',
            'latitude',
            'longitude',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        restaurant_name = validated_data.pop('restaurant_name')
        address = validated_data.pop('address', '')
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)

        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(
            user=user,
            restaurant_name=restaurant_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        return user


# ─────────────────────────────────────────────
# 🆕 Register View
# ─────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            profile = user.profile
            return Response({
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "restaurant_name": profile.restaurant_name,
                    "position": profile.position,
                    "address": profile.address,
                    "latitude": profile.latitude,
                    "longitude": profile.longitude,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 👀 "Me" endpoint — return current user info
# ─────────────────────────────────────────────
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "restaurant_name": profile.restaurant_name,
            "position": profile.position,
            "address": profile.address,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
        })
