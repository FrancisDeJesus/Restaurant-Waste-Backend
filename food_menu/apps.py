# food_menu/apps.py
from django.apps import AppConfig

class FoodMenuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'food_menu'

    def ready(self):
        from . import signals  # 👈 we'll handle the auto-create logic here
