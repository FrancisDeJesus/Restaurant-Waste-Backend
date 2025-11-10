# analytics/urls.py
from django.urls import path
from .views import VolumeWasteAnalyticsView

urlpatterns = [
    path('volume/', VolumeWasteAnalyticsView.as_view(), name='volume-analytics'),
]
