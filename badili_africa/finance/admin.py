from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Project, Expense

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'alias', 'designation']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('alias', 'designation')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('alias', 'designation')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Project)
admin.site.register(Expense)