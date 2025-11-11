# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg
from trash_pickups.models import TrashPickup
from employees.models import Employee
from datetime import datetime


class VolumeWasteAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # Restaurant owner

        # ======================================================
        # ♻️ Filter: Only pickups belonging to this restaurant
        # ======================================================
        pickups = TrashPickup.objects.filter(user=user)

        # ======================================================
        # 1️⃣ Weekly Waste Trends
        # ======================================================
        weekly_data = (
            pickups.extra({'week': "strftime('%%W', created_at)"})
            .values('week')
            .annotate(total_weight=Sum('weight_kg'))
            .order_by('week')
        )

        # ======================================================
        # 2️⃣ Waste Type Breakdown
        # ======================================================
        waste_type_data = (
            pickups.values('waste_type')
            .annotate(total=Sum('weight_kg'))
            .order_by('-total')
        )

        # ======================================================
        # 3️⃣ Pickup Frequency
        # ======================================================
        pickup_frequency = pickups.count()

        # ======================================================
        # 4️⃣ Segregation Accuracy (avg segregation_score)
        # ======================================================
        segregation_accuracy = (
            pickups.aggregate(accuracy=Avg('segregation_score')).get('accuracy') or 0
        )

        # ======================================================
        # 5️⃣ Employee Activity
        # ======================================================
        employees = Employee.objects.filter(owner=user)
        employee_activity_counts = {
            emp.name: pickups.filter(driver__id=emp.id).count() for emp in employees
        }

        # ======================================================
        # 6️⃣ Monthly Waste & Reward Eligibility
        # ======================================================
        now = datetime.now()
        monthly_total = (
            pickups.filter(
                created_at__month=now.month,
                created_at__year=now.year
            ).aggregate(total_weight=Sum('weight_kg')).get('total_weight') or 0
        )

        # 🚫 Define your threshold here (adjust anytime)
        waste_limit = 500.0  # 500 kg per month max
        eligible_for_rewards = monthly_total <= waste_limit

        # ======================================================
        # 📦 Response Payload
        # ======================================================
        data = {
            "waste_volume_trends": list(weekly_data),
            "waste_type_breakdown": list(waste_type_data),
            "pickup_frequency": pickup_frequency,
            "segregation_accuracy": round(segregation_accuracy, 2),
            "employee_activity_counts": employee_activity_counts,
            "total_monthly_waste": float(monthly_total),
            "waste_limit": waste_limit,
            "eligible_for_rewards": eligible_for_rewards,
        }

        return Response(data)
