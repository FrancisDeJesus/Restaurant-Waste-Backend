# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg
from trash_pickups.models import TrashPickup
from employees.models import Employee
from datetime import datetime, timedelta

class VolumeWasteAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Restaurant owner

        # Filter by restaurant/user
        pickups = TrashPickup.objects.filter(user=user)

        # --- 1️⃣ Waste Volume Trends ---
        # Count or sum of waste by week (example)
        weekly_data = (
            pickups.extra({'week': "strftime('%%W', created_at)"})
            .values('week')
            .annotate(total_weight=Sum('weight_kg'))
            .order_by('week')
        )

        # --- 2️⃣ Waste Type Breakdown ---
        waste_type_data = (
            pickups.values('waste_type')
            .annotate(total=Sum('weight_kg'))
            .order_by('-total')
        )

        # --- 3️⃣ Pickup Frequency ---
        pickup_frequency = pickups.count()

        # --- 4️⃣ Segregation Accuracy (dummy example if you have that field) ---
        segregation_accuracy = pickups.aggregate(accuracy=Avg('segregation_score')).get('accuracy') or 0

        # --- 5️⃣ Employee Activity Counts ---
        employees = Employee.objects.filter(owner=user)
        employee_activity_counts = {
            emp.name: pickups.filter(employee=emp).count() for emp in employees
        }

        data = {
            "waste_volume_trends": list(weekly_data),
            "waste_type_breakdown": list(waste_type_data),
            "pickup_frequency": pickup_frequency,
            "segregation_accuracy": round(segregation_accuracy, 2),
            "employee_activity_counts": employee_activity_counts,
        }

        return Response(data)
