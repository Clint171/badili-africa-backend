from django.db import models

class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100)
    dob = models.DateField()
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

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
    project = models.ForeignKey(Project, on_delete=models.CASCADE , default=None)
    activity = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    receipt = models.FileField(upload_to="receipts/")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE , default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_name} - {self.amount}"
