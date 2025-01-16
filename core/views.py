from django.shortcuts import render, redirect
from .models import HospitalBranches, Users
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from .serializers import HospitalBranchSerializer, UserSerializer
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def home(request):
    return render(request, "home.html")

def docProfile(request):
    return render(request, "docProfile.html")

def patientProfile(request):
    return render(request,"patientProfile.html")

def adminDB(request):
    return render(request, "adminDB.html")

def masterAdmin(request):
    if request.user.role != "masterAdmin":
        return redirect('login')
    return render(request, "masterAdmin.html")


def loginPage(request):
    if request.GET:
        return redirect("/login/")
    return render(request, "login.html")

# Login
@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        email = data.get('email')
        password = data.get('password')

        # Validate inputs
        if not email or not password:
            return JsonResponse({'error': 'Email and Password are required'}, status=400)

        try:
            # Fetch user from the database
            user = Users.objects.get(email=email)

            # Check password
            if not check_password(password, user.password):
                return JsonResponse({'error': 'Invalid password'}, status=401)

            # Redirect based on role
            if user.role == 'masterAdmin':
                return JsonResponse({'success': True, 'redirect_url': '/masterAdminDB/'}, status=200)

            elif user.role == 'Doctor':
                return JsonResponse({'success': True, 'redirect_url': ''}, status=200)

            elif user.role == 'Admin':
                return JsonResponse({'success': True, 'redirect_url': '/adminDB/'}, status=200)

            elif user.role == 'Patient':
                return JsonResponse({'success': True, 'redirect_url': ''}, status=200)

            elif user.role == 'Reception':
                return JsonResponse({'success': True, 'redirect_url': '/receptionDB/'}, status=200)

            elif user.role == 'TestCentre':
                return JsonResponse({'success': True, 'redirect_url': '/testCentreDB/'}, status=200)

            # If role does not match any known role
            return JsonResponse({'error': 'Unauthorized role'}, status=403)

        except Users.DoesNotExist:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

    return JsonResponse({'error': 'Invalid request method'}, status=405)




# Hospital CRUD
class HospitalBranchView(APIView):
    def get(self, request):
        branches = HospitalBranches.objects.all()
        serializer = HospitalBranchSerializer(branches, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = HospitalBranchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            branch = HospitalBranches.objects.get(pk=pk)
        except HospitalBranches.DoesNotExist:
            return Response({'error': 'Hospital Branch not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = HospitalBranchSerializer(branch, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            branch = HospitalBranches.objects.get(pk=pk)
            branch.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except HospitalBranches.DoesNotExist:
            return Response({'error': 'Hospital Branch not found'}, status=status.HTTP_404_NOT_FOUND)


# Admin CRUD
class AdminView(APIView):
    def get(self, request):
        admins = Users.objects.filter(role='Admin')
        serializer = UserSerializer(admins, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            admin = Users.objects.get(pk=pk, role='Admin')
        except Users.DoesNotExist:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSerializer(admin, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            admin = Users.objects.get(pk=pk, role='Admin')
            admin.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Users.DoesNotExist:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)