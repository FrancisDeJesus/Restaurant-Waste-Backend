# donation_drive/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DonationDriveViewSet

router = DefaultRouter()
router.register(r'donation_drive', DonationDriveViewSet, basename='donation-drive')

urlpatterns = [
    path('', include(router.urls)),
]
