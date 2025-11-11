# employees/models.py
from django.db import models
from django.contrib.auth.models import User  # ✅ import User

class Employee(models.Model):
    # 🔗 Link each employee to a restaurant (User)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="employees",
        help_text="The restaurant owner who manages this employee"
    )

    name = models.CharField(max_length=100)
    position = models.CharField(max_length=50)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    date_hired = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.position}"
