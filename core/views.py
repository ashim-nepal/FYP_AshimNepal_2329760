from django.shortcuts import render, redirect
from .models import HospitalBranches, Users
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from .serializers import HospitalBranchSerializer, UserSerializer
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.utils.timezone import now

# Create your views here.
def home(request):
    return render(request, "home.html")

def docProfile(request):
    return render(request, "docProfile.html")

def patientProfile(request):
    return render(request,"patientProfile.html")

def adminDB(request):
    return render(request, "adminDB.html")

def receptionDB(request):
    if request.user.role != "Reception":
        return redirect('login')
    return render(request, "receptionDB.html", {'role': request.user.role})

# @login_required(login_url='/login/')  # ✅ Ensure only logged-in users can access
# def masterAdmin(request):
#     # ✅ Check if session exists
#     if 'user_id' not in request.session:
#         return redirect('/login/')

#     return render(request, 'masterAdmin.html')

def masterAdmin(request):
    if not request.session.get('is_authenticated'):
        return redirect('/login/')
    
    if request.session.get('user_role') != 'masteradmin':
        return redirect('/login/')  # Prevent unauthorized access
    
    return render(request, 'masterAdmin.html')


def loginPage(request):
    if request.GET:
        return redirect("/login/")
    return render(request, "login.html")

# Login
@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return JsonResponse({'error': 'Email and Password are required'}, status=400)

            user = Users.objects.filter(email=email).first()
            print("User Found: ",user)
            print("User Role: ",user.role)

            if user and check_password(password, user.password):
                
                request.session['user_id'] = str(user.id)
                request.session['user_role'] = user.role.lower()
                request.session.set_expiry(86400)
                
                
                request.session['is_authenticated'] = True
                

                # ✅ Redirect user based on role
                role_redirects = {
                    'masteradmin': '/masterAdminDB/',
                    'doctor': '/doctorDB/',
                    'admin': '/adminDB/',
                    'patient': '/patientDB/',
                    'reception': '/receptionDB/',
                    'testcentre': '/testCentreDB/',
                }

                return JsonResponse({'success': True, 'redirect_url': role_redirects.get(user.role.lower(), '/')}, status=200)

            return JsonResponse({'error': 'Invalid email or password'}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Users.objects.get(email=email)
            if check_password(password, user.password):
                request.session['user_id'] = str(user.id)  # Store user in session
                request.session['user_role'] = user.role.lower()
                request.session.set_expiry(86400)

                # Role-based redirect
                role_redirects = {
                    'masteradmin': '/masterAdminDB/',
                    'doctor': '/doctorDB/',
                    'admin': '/adminDB/',
                    'patient': '/patientDB/',
                    'reception': '/receptionDB/',
                    'testcentre': '/testCentreDB/',
                }
                return redirect(role_redirects.get(user.role.lower(), '/'))

        except Users.DoesNotExist:
            return render(request, 'login.html', {'error': 'Invalid email or password'})

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('/login/')


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
        
        

# def create_user_view(request):
#     email = 'masteradmin@sync.com'
#     password = 'Master@123456'
#     name = 'System Master Admin'
#     role = 'masterAdmin'
#     is_active = True

#     new_user = Users(
#         email=email,
#         password=make_password(password),
#         name=name,
#         role=role,
#         is_active=is_active
#     )
#     new_user.save()
#     return HttpResponse('User  created successfully.')