from django.shortcuts import render
from rest_framework import viewsets
from .models import FundingSource, Stipulation, Project, CostCenter
from .serializers import FundingSourceSerializer, StipulationSerializer, ProjectSerializer, CostCenterSerializer

class FundingSourceViewSet(viewsets.ModelViewSet):
    queryset = FundingSource.objects.all()
    serializer_class = FundingSourceSerializer

class StipulationViewSet(viewsets.ModelViewSet):
    queryset = Stipulation.objects.all()
    serializer_class = StipulationSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class CostCenterViewSet(viewsets.ModelViewSet):
    queryset = CostCenter.objects.all()
    serializer_class = CostCenterSerializer
