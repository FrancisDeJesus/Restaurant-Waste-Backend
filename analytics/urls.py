# analytics/urls.py
from django.urls import path
from .views import (
    VolumeWasteAnalyticsView,
    TodayWasteSummaryView,
    EfficiencyScoreView,
)

urlpatterns = [
    path('volume/', VolumeWasteAnalyticsView.as_view(), name='volume-analytics'),
    path('today/', TodayWasteSummaryView.as_view(), name='today-waste'),
    path('efficiency/', EfficiencyScoreView.as_view(), name='efficiency-score'),
    
]
