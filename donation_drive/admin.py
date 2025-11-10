from django.contrib import admin
from .models import DonationDrive, Donation

@admin.register(DonationDrive)
class DonationDriveAdmin(admin.ModelAdmin):
    list_display = ('title', 'waste_type', 'is_active', 'created_at')
    list_filter = ('waste_type', 'is_active')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('drive', 'waste_type', 'weight_kg', 'donated_at')
    list_filter = ('waste_type', 'drive')
    ordering = ('-donated_at',)
    readonly_fields = ('donated_at',)
