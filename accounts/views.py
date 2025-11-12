# accounts/views.py
from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from .firebase_config import auth as firebase_auth
from .serializers import UserProfileSerializer


from .models import UserProfile
from drivers.models import Driver


# ============================================================
# 👤 REGISTRATION SERIALIZER
# ============================================================
class RegisterSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "restaurant_name",
            "address",
            "latitude",
            "longitude",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        restaurant_name = validated_data.pop("restaurant_name")
        address = validated_data.pop("address", "")
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(
            user=user,
            restaurant_name=restaurant_name,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        return user


# ============================================================
# 🆕 REGISTER VIEW
# ============================================================
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("🧭 Incoming registration data:", request.data)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            profile = getattr(user, "profile", None)

            return Response(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "restaurant_name": getattr(profile, "restaurant_name", None),
                        "position": getattr(profile, "position", None),
                        "address": getattr(profile, "address", None),
                        "latitude": getattr(profile, "latitude", None),
                        "longitude": getattr(profile, "longitude", None),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================
# 👀 "ME" ENDPOINT — RETURN CURRENT USER INFO
# ============================================================
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "profile", None)
        driver_profile = getattr(request.user, "driver_profile", None)

        if driver_profile:
            return Response(
                {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "role": "driver",
                    "driver_id": driver_profile.id,
                    "full_name": driver_profile.full_name,
                    "vehicle_type": driver_profile.vehicle_type,
                }
            )

        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "restaurant_name": getattr(profile, "restaurant_name", None),
                "position": getattr(profile, "position", None),
                "address": getattr(profile, "address", None),
                "latitude": getattr(profile, "latitude", None),
                "longitude": getattr(profile, "longitude", None),
                "role": "restaurant",
            }
        )


# ============================================================
# 🚚 DRIVER LOGIN — Custom JWT for Driver model
# ============================================================
@method_decorator(csrf_exempt, name="dispatch")
class DriverTokenObtainPairView(APIView):
    """
    Allows Driver model users to log in using their username and password
    and receive JWT tokens compatible with SimpleJWT.
    """
    authentication_classes = []  # ✅ public endpoint
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("📩 DRIVER LOGIN ATTEMPT:", request.data)
        serializer = DriverTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ============================================================
# 🚛 DRIVER JWT SERIALIZER (FIXED)
# ============================================================
class DriverTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        # 🔍 Step 1: Try to find the driver record
        try:
            driver = Driver.objects.get(username=username, is_active=True)
        except Driver.DoesNotExist:
            raise serializers.ValidationError("No active driver found with that username.")

        # 🔐 Step 2: Verify password
        if not driver.verify_password(password):
            raise serializers.ValidationError("Invalid password.")

        # ✅ Step 3: Ensure a linked User exists for JWT
        if not driver.user:
            user = User.objects.create_user(username=username, password=password)
            driver.user = user
            driver.save()
        else:
            user = driver.user
            # Sync password if changed
            if not user.check_password(password):
                user.set_password(password)
            user.is_active = True
            user.save()

        # 🎟️ Step 4: Generate JWT
        refresh = RefreshToken.for_user(user)

        # ✅ Step 5: Return token + driver info
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "driver_id": driver.id,
            "full_name": driver.full_name,
        }
# ------------------GOOGLE LOG IN ---------------------------------

class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            # ✅ Accept any possible key name from frontend
            firebase_token = (
                request.data.get("firebase_token")
                or request.data.get("token")
                or request.data.get("idToken")
                or request.data.get("credential")
            )

            if not firebase_token:
                return Response(
                    {"error": "Missing Firebase token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ Verify token with Firebase Admin SDK
            decoded = firebase_auth.verify_id_token(firebase_token)
            email = decoded.get("email")
            name = decoded.get("name", "Google User")
            uid = decoded.get("uid")

            if not email:
                return Response(
                    {"error": "Email not found in token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ✅ Create or get Django user
            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": name},
            )

            # ✅ Ensure linked UserProfile exists
            profile, prof_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    "restaurant_name": name,
                    "address": "Signed up with Google",
                    "latitude": None,
                    "longitude": None,
                },
            )

            # ✅ Issue JWT tokens (SimpleJWT)
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "name": user.first_name,
                    "restaurant_name": profile.restaurant_name,
                    "address": profile.address,
                    "latitude": profile.latitude,
                    "longitude": profile.longitude,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "new_user": created,
                    "new_profile": prof_created,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
# ============================================================
# ⚙️ USER PROFILE UPDATE VIEW
# ============================================================
class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Allows the logged-in user to view and edit their own profile details.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # Always return the current user's profile
        return self.request.user.profile
        