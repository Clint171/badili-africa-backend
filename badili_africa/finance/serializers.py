from rest_framework import serializers
from .models import FundingSource, Stipulation, Project, CostCenter

class FundingSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingSource
        fields = '__all__'

class StipulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stipulation
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'
