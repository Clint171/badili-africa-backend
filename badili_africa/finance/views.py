from django.shortcuts import render
from rest_framework import viewsets
from .models import Expense , User , Project
from .serializers import ExpenseSourceSerializer


# CRUD views

class ExpenseSourceViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSourceSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = ExpenseSourceSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ExpenseSourceSerializer

# Custom views

def get_expenses_by_project(request, project_id):
    expenses = Expense.objects.filter(project=project_id)

    ## Should return json
    return expenses
