from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    alias = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    # Add related_name to resolve conflicts
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",
        related_query_name="user",
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    activities = models.TextField()
    status = models.CharField(max_length=100 , default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Expense(models.Model):
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE, default=None)
    project_name = models.CharField(max_length=100)
    activity = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    receipt = models.FileField(upload_to="receipts/")
    project_officer_id = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    project_officer = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project_id.name} - {self.amount}"