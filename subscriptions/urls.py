# subscriptions/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionPlanViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'plans', SubscriptionPlanViewSet, basename='subscription-plans')

urlpatterns = [
    path('', include(router.urls)),

    # ✅ Correct endpoints for ViewSet actions
    path(
        'manage/active/',
        SubscriptionViewSet.as_view({'get': 'active'}),
        name='subscription-active'
    ),
    path(
        'manage/subscribe/',
        SubscriptionViewSet.as_view({'post': 'subscribe'}),
        name='subscription-subscribe'
    ),
    path(
        'manage/history/',
        SubscriptionViewSet.as_view({'get': 'history'}),
        name='subscription-history'
    ),
]
