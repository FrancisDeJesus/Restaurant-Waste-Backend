# employees/serializers.py
from rest_framework import serializers
from .models import Employee

class EmployeeSerializer(serializers.ModelSerializer):
    
    owner_name = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['date_hired', 'updated_at', 'owner']
