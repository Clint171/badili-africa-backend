from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets
from .models import Expense , User , Project
from .serializers import ExpenseSerializer , UserSerializer , ProjectSerializer


# CRUD views

class ExpenseSourceViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

# Custom views

def get_expenses_by_project(request, project_id):
    expenses = Expense.objects.filter(project=project_id)
    serializer = ExpenseSerializer(expenses, many=True)
    return JsonResponse(serializer.data, safe=False)
