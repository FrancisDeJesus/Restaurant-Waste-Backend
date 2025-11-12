# analytics/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg
from django.utils.timezone import now
from trash_pickups.models import TrashPickup
from employees.models import Employee
from datetime import datetime


# ===============================================================
# 📊 1. VOLUME & WASTE ANALYTICS
# ===============================================================
class VolumeWasteAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  # ✅ fixed typo (was request.use)
        pickups = TrashPickup.objects.filter(user=user)

        # 1️⃣ Weekly Waste Trends
        weekly_data = (
            pickups.extra({'week': "strftime('%%W', created_at)"})
            .values('week')
            .annotate(total_weight=Sum('weight_kg'))
            .order_by('week')
        )

        # 2️⃣ Waste Type Breakdown
        waste_type_data = (
            pickups.values('waste_type')
            .annotate(total=Sum('weight_kg'))
            .order_by('-total')
        )

        # 3️⃣ Pickup Frequency
        pickup_frequency = pickups.count()

        # 4️⃣ Segregation Accuracy
        segregation_accuracy = (
            pickups.aggregate(accuracy=Avg('segregation_score')).get('accuracy') or 0
        )

        # 5️⃣ Employee Activity
        employees = Employee.objects.filter(owner=user)
        employee_activity_counts = {
            emp.name: pickups.filter(driver__id=emp.id).count() for emp in employees
        }

        # 6️⃣ Monthly Waste & Reward Eligibility
        now_dt = datetime.now()
        monthly_total = (
            pickups.filter(
                created_at__month=now_dt.month,
                created_at__year=now_dt.year
            ).aggregate(total_weight=Sum('weight_kg')).get('total_weight') or 0
        )

        waste_limit = 500.0
        eligible_for_rewards = monthly_total <= waste_limit

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


# ===============================================================
# ♻️ 2. TODAY'S WASTE SUMMARY
# ===============================================================
class TodayWasteSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()

        total_today = (
            TrashPickup.objects.filter(
                user=user,
                status='completed',
                completed_at__date=today
            ).aggregate(total=Sum('weight_kg')).get('total') or 0
        )

        return Response({
            "date": today,
            "total_kg": round(total_today, 2)
        })


# ===============================================================
# 💡 3. EFFICIENCY SCORE
# ===============================================================
class EfficiencyScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        pickups = TrashPickup.objects.filter(user=user)
        total_pickups = pickups.count()
        completed_pickups = pickups.filter(status='completed').count()
        avg_segregation = (
            pickups.aggregate(avg=Avg('segregation_score')).get('avg') or 0
        )

        if total_pickups == 0:
            efficiency = 0
        else:
            completion_rate = completed_pickups / total_pickups
            efficiency = (completion_rate * 0.6 + (avg_segregation / 100) * 0.4) * 100

        return Response({
            "efficiency_score": round(efficiency, 1)
        })
