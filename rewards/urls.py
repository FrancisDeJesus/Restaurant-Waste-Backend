from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RewardViewSet, RedeemedHistoryListView

router = DefaultRouter()
router.register(r'rewards', RewardViewSet, basename='rewards')

urlpatterns = [
    path('', include(router.urls)),
    path('redeemed/', RedeemedHistoryListView.as_view(), name='redeemed-history'),  
   
]
