from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationDriveViewSet, DonationViewSet

router = DefaultRouter()
router.register(r'donation_drives', DonationDriveViewSet, basename='donation-drive')
router.register(r'donations', DonationViewSet, basename='donation')

urlpatterns = [
    path('', include(router.urls)),
]
