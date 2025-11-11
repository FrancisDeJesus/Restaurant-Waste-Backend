from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from .models import Employee
from .serializers import EmployeeSerializer


# =========================================================
# 🧑‍💼 EMPLOYEE VIEWSET (For DRF routers)
# =========================================================
class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Each logged-in restaurant owner only sees their employees.
        """
        return Employee.objects.filter(owner=self.request.user).order_by('id')

    def perform_create(self, serializer):
        """
        Automatically link the logged-in restaurant (User) as the owner.
        """
        serializer.save(owner=self.request.user)


# =========================================================
# 🧾 FUNCTION-BASED CRUD VIEWS (if you use them separately)
# =========================================================

# --------------------- READ EMPLOYEES --------------------
@api_view(['GET'])
def employee_list(request):
    employees = Employee.objects.filter(owner=request.user).order_by('id')
    serializer = EmployeeSerializer(employees, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# --------------------- CREATE EMPLOYEES --------------------
@api_view(['POST'])
def employee_create(request):
    serializer = EmployeeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)  # ✅ Auto-assign owner
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------- UPDATE EMPLOYEES --------------------
@api_view(['PUT', 'PATCH'])
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk, owner=request.user)  # ✅ Only your employees
    serializer = EmployeeSerializer(employee, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --------------------- DELETE EMPLOYEES --------------------
@api_view(['DELETE'])
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk, owner=request.user)  # ✅ Restrict to your employees
    employee.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
