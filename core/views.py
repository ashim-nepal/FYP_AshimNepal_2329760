from django.shortcuts import render, redirect, get_object_or_404
from .models import HospitalBranches, Users, Doctors, Departments
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
import json
from .serializers import HospitalBranchSerializer, UserSerializer
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

# Create your views here.
def home(request):
    return render(request, "home.html")

def docProfile(request):
    return render(request, "docProfile.html")

def patientProfile(request):
    return render(request,"patientProfile.html")

def adminDB(request):
    if not request.session.get('is_authenticated'):
        return redirect('/login/')
    
    if request.session.get('user_role') != 'admin':
        return redirect('/login/')  # Prevent unauthorized access
    
    #Get admin details from session
    admin_id = request.session.get('user_id')
    admin = Users.objects.get(id=admin_id)

    # Get hospital name based on admin's branch_id
    hospital_name = "Unknown Hospital"
    if admin.branch:
        branch = HospitalBranches.objects.get(branch_code=admin.branch.branch_code)
        hospital_name = branch.branch_name  # Fetch the hospital name
        hospital_branch = branch.branch_code
    
    return render(request, 'adminDB.html', {'branch_name': hospital_name, 'branch_code': hospital_branch})

def receptionDB(request):
    if not request.session.get('is_authenticated'):
        return redirect('/login/')
    
    if request.session.get('user_role') != 'reception':
        return redirect('/login/')  # Prevent unauthorized access
    
    #Get admin details from session
    reception_id = request.session.get('user_id')
    receptionist = Users.objects.get(id=reception_id)

    # Get hospital name based on admin's branch_id
    hospital_name = "Unknown Hospital"
    if receptionist.branch:
        branch = HospitalBranches.objects.get(branch_code=receptionist.branch.branch_code)
        hospital_name = branch.branch_name  # Fetch the hospital name
        hospital_branch = branch.branch_code
    return render(request, "receptionDB.html", {'branch_name': hospital_name, 'branch_code': hospital_branch})


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

# Master Admin functions
# Hospital CRUD
def get_hospital_branches(request):
    branches = list(HospitalBranches.objects.values())
    return JsonResponse({'branches': branches}, safe=False)

# Adding new hospital branch data
@csrf_exempt
def add_hospital_branch(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            branch = HospitalBranches.objects.create(
                branch_name=data.get("branch_name"),
                branch_location=data.get("branch_location"),
                branch_code=data.get("branch_code")
            )
            return JsonResponse({"success": True, "message": "Hospital branch added successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        
# Edit Hospital branch
@csrf_exempt
def edit_hospital_branch(request, branch_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            branch = HospitalBranches.objects.get(id=branch_id)
            branch.branch_name = data.get("branch_name", branch.branch_name)
            branch.branch_location = data.get("branch_location", branch.branch_location)
            branch.branch_code = data.get("branch_code", branch.branch_code)
            branch.save()
            return JsonResponse({"success": True, "message": "Hospital branch updated successfully!"})
        except HospitalBranches.DoesNotExist:
            return JsonResponse({"error": "Branch not found"}, status=404)
        

# Delete a hospital branch
@csrf_exempt
def delete_hospital_branch(request, branch_id):
    if request.method == 'DELETE':
        try:
            branch = HospitalBranches.objects.get(id=branch_id)
            branch.delete()
            return JsonResponse({"success": True, "message": "Hospital branch deleted successfully!"})
        except HospitalBranches.DoesNotExist:
            return JsonResponse({"error": "Branch not found"}, status=404)


# Admin CRUD
#Fetch all admins
def get_admins(request):
    admins = list(Users.objects.filter(role="Admin").values("id", "name", "email", "branch_id", "is_active"))
    return JsonResponse({'admins': admins}, safe=False)


#Add a new admin
@csrf_exempt
def add_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            hashed_password = make_password(data.get("password"))  # Encrypt password before storing
            print(data)

            admin = Users.objects.create(
                name=data.get("name"),
                email=data.get("email"),
                password=hashed_password,
                role="Admin",
                branch_id=data.get("branch_id"),
                is_active=True
            )
            return JsonResponse({"success": True, "message": "Admin added successfully!"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        
#Edit existing admin        
@csrf_exempt
def edit_admin(request, admin_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            admin = Users.objects.get(id=admin_id)

            admin.name = data.get("name", admin.name)
            admin.email = data.get("email", admin.email)
            if "password" in data and data["password"]:
                admin.password = make_password(data["password"])  # Hash new password
            
            admin.save()
            return JsonResponse({"success": True, "message": "Admin updated successfully!"})
        except Users.DoesNotExist:
            return JsonResponse({"error": "Admin not found"}, status=404)
        
#Delete an admin
@csrf_exempt
def delete_admin(request, admin_id):
    if request.method == 'DELETE':
        try:
            admin = Users.objects.get(id=admin_id)
            admin.delete()
            return JsonResponse({"success": True, "message": "Admin deleted successfully!"})
        except Users.DoesNotExist:
            return JsonResponse({"error": "Admin not found"}, status=404)




# Admin Dashboard Features


# Add Receptionist (Users Table)
@csrf_exempt
def add_receptionist(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        try:
            receptionist = Users.objects.create(
                name=data['name'],
                email=data['email'],
                password=make_password(data['password']),
                role="Reception",
                branch_id=data['branch_id'],
                is_active=True
            )
            return JsonResponse({"success": True, "message": "Receptionist added successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)



#Add Doctor (Users & Doctors Table)
@csrf_exempt
def add_doctor(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
            # Handle Form Data (Multipart Form Submission)
                name = request.POST.get('name')
                email = request.POST.get('email')
                password = request.POST.get('password')
                department= request.POST.get('department')
                branch_id = request.POST.get('branch_id')
                nmc = request.POST.get('nmc')
                expertise = request.POST.get('expertise')
                education = request.POST.get('education')
                hospitals_worked = request.POST.get('hospitals_worked')
                achievements = request.POST.get('achievements')
                profile_pic = request.FILES.get('profile_pic')  # Fetch image file

                # Validate Required Fields
                if not all([name, email, password, department, branch_id, nmc]):
                    return JsonResponse({"error": "All fields are required!"}, status=400)

                # Ensure Branch Exists
                try:
                    branch = HospitalBranches.objects.get(branch_code=branch_id)
                except HospitalBranches.DoesNotExist:
                    return JsonResponse({"error": "Invalid Branch ID"}, status=400)

                # Ensure Department Exists
                try:
                    department = Departments.objects.get(name=department)
                except Departments.DoesNotExist:
                    return JsonResponse({"error": "Invalid Department ID"}, status=400)

                # Save User (Doctor) in Users Table
                user = Users.objects.create(
                    name=name,
                    email=email,
                    password=make_password(password),
                    role="Doctor",
                    branch=branch,
                    is_active=True,
                    profile_pic=profile_pic
                )

                #  Save Doctor Details in Doctors Table
                Doctors.objects.create(
                    # user=user,
                    department=department,
                    branch_id=branch_id,
                    nmc_registration=nmc,
                    expertise=expertise,
                    education=education,
                    hospitals_worked=hospitals_worked,
                    name=name,
                    achievements=achievements,
                )

                return JsonResponse({"success": True, "message": "Doctor added successfully."}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# Add Department (Stored in Departments Table)
@csrf_exempt
def add_department(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            branch_id = request.POST.get('branch_id')
            image = request.FILES.get('image')  # Handling the image file

            # Validate required fields
            if not name or not branch_id:
                return JsonResponse({'error': 'Name and Branch ID are required'}, status=400)

            # Ensure the branch exists
            try:
                branch = HospitalBranches.objects.get(branch_code=branch_id)
            except HospitalBranches.DoesNotExist:
                return JsonResponse({'error': 'Invalid branch ID'}, status=400)
        

            # Create department
            department = Departments.objects.create(
                name=name,
                description=description,
                branch=branch,
                image=image  # Save the image file
            )

            return JsonResponse({'message': 'Department added successfully!', 'department_id': department.id}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
        

# Get All Users (Receptionists & Doctors)
def get_users(request):
    users = Users.objects.filter(role__in=['Reception', 'Doctor']).values('id', 'name', 'email', 'role', 'branch_id')
    return JsonResponse(list(users), safe=False)

# Get All Departments
def get_departments(request):
    try:
        departments = Departments.objects.all().values('id', 'name', 'description')
        return JsonResponse({"departments": list(departments)}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Edit User (Receptionist or Doctor)
@csrf_exempt
def edit_user(request, user_id):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        user = get_object_or_404(Users, id=user_id)
        user.name = data['name']
        user.email = data['email']
        user.save()

        # If Doctor, update Doctors Table too
        if user.role == "Doctor":
            doctor = get_object_or_404(Doctors, user=user)
            doctor.expertise = data['expertise']
            doctor.education = data['education']
            doctor.hospitals_worked = data['hospitals_worked']
            doctor.achievements = data['achievements']
            doctor.save()

        return JsonResponse({"success": True, "message": "User updated successfully."})


# Delete User (Receptionist or Doctor)
@csrf_exempt
def delete_user(request, user_id):
    user = get_object_or_404(Users, id=user_id)
    user.delete()
    return JsonResponse({"success": True, "message": "User deleted successfully."})


# Edit Department
@csrf_exempt
def edit_department(request, dept_id):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        dept = get_object_or_404(Departments, id=dept_id)
        dept.name = data['name']
        dept.description = data['description']
        dept.save()
        return JsonResponse({"success": True, "message": "Department updated successfully."})

# Delete Department
@csrf_exempt
def delete_department(request, dept_id):
    dept = get_object_or_404(Departments, id=dept_id)
    dept.delete()
    return JsonResponse({"success": True, "message": "Department deleted successfully."})

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