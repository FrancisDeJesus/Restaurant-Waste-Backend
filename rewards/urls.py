from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RewardViewSet, RewardRedemptionViewSet

router = DefaultRouter()
router.register(r'rewards', RewardViewSet, basename='reward')
router.register(r'redeem', RewardRedemptionViewSet, basename='reward-redemption')

urlpatterns = [
    path('', include(router.urls)),
]
