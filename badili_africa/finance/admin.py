from django.contrib import admin
from .models import FundingSource, Stipulation, Project, CostCenter

admin.site.register(FundingSource)
admin.site.register(Stipulation)
admin.site.register(Project)
admin.site.register(CostCenter)
