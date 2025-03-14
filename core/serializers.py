from rest_framework import serializers
from .models import HospitalBranches, Users, DoctorAvailability, Appointments

class HospitalBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalBranches
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.branch_name', read_only=True)

    class Meta:
        model = Users
        fields = ['id', 'name', 'email', 'branch', 'branch_name', 'is_active', 'created_at']
        

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointments
        fields = '__all__'