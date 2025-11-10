# drivers/admin.py
from django.contrib import admin
from .models import Driver

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "username",
        "contact_number",
        "vehicle_type",
        "license_number",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "vehicle_type", "created_at")
    search_fields = ("full_name", "username", "contact_number", "license_number")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
