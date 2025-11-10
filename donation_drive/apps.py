from django.apps import AppConfig

class DonationDriveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'donation_drive'

    def ready(self):
        import donation_drive.signals
