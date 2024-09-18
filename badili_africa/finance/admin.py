from django.contrib import admin
from .models import Expense , User , Project

admin.site.register(User)
admin.site.register(Project)
admin.site.register(Expense)
