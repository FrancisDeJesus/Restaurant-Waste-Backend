from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, MeView, DriverTokenObtainPairView, GoogleAuthView, UserProfileUpdateView

urlpatterns = [
    # 🔐 User authentication (for restaurants/employees)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 🆕 Registration and profile routes
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
    path('profile/', UserProfileUpdateView.as_view(), name='profile-update'),
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    # 🚚 Driver login route
    path('driver/token/', DriverTokenObtainPairView.as_view(), name='driver_token'),
    
]
