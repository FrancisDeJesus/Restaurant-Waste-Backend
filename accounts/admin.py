# accounts/admin.py
from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant_name', 'position', 'address') 
    search_fields = ('user__username', 'restaurant_name', 'address')
    list_filter = ('position',)
    ordering = ('user__username',)

    fieldsets = (
        ("User Info", {"fields": ("user", "restaurant_name", "position", "address")}),
    )
