from rest_framework import serializers
from .models import HospitalBranches, Users

class HospitalBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalBranches
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)

    class Meta:
        model = Users
        fields = ['id', 'name', 'email', 'branch', 'branch_name', 'is_active', 'created_at']