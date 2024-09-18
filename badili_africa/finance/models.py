from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    alias = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Project(models.Model):
    project_name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name

class Expense(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    activity = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    receipt = models.FileField(upload_to="receipts/")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.project_name} - {self.amount}"