from django.contrib import admin
from .models import DonationDrive

@admin.register(DonationDrive)
class DonationDriveAdmin(admin.ModelAdmin):
    list_display = ('title', 'waste_type', 'is_active', 'created_at')
    list_filter = ('waste_type', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
