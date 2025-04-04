from django.shortcuts import render, redirect, get_object_or_404
from .models import HospitalBranches, Users, Doctors, Departments, Patients, HealthPackages, TestCentre, Banners, DoctorAvailability, Appointments, Reviews, Prescriptions, TestResults, TestBooking, HealthPackageBookings
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json, uuid, datetime
from datetime import datetime, timedelta, date
from .serializers import HospitalBranchSerializer, UserSerializer, DoctorAvailabilitySerializer, AppointmentSerializer
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Avg, Count
from django.utils.dateparse import parse_date
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.dateparse import parse_time
from django.core.files.base import ContentFile


# Create your views here.
def home(request):
    return render(request, "home.html")


def patientProfile(request):
    if not request.session.get('is_authenticated'):
        return redirect('/login/')
    
    if request.session.get('user_role') != 'patient':
        return redirect('/login/')  # Prevent unauthorized access
    
    user_email = request.session.get('user_email')
    print(user_email)
    
    #Get admin details from session
    patient_id = request.session.get('user_id')
    patient = Users.objects.get(id=patient_id)

    # Get hospital name based on admin's branch_id
    hospital_name = "Unknown Hospital"
    if patient.branch:
        branch = HospitalBranches.objects.get(branch_code=patient.branch.branch_code)
        hospital_name = branch.branch_name  # Fetch the hospital name
        hospital_branch = branch.branch_code
        try:
            patient_val = Patients.objects.get(email=user_email)
        except Patients.DoesNotExist:
            patient_val = None
        
        patient_val.assigned_doctors_data = json.loads(patient_val.assigned_doctors)
        print(patient_val.assigned_doctors_data)
    return render(request,"patientProfile.html", {'branch_name': hospital_name, 'branch_code': hospital_branch, 'patients': patient_val})


def doctorProfilePage(request):
    if not request.session.get('is_authenticated'):
        return redirect('/login/')
    
    if request.session.get('user_role') != 'doctor':
        return redirect('/login/')  # Prevent unauthorized access
    
    
    
    user_email = request.session.get('user_email')
    print(user_email)
    
    #Get admin details from session
    doctor_id = request.session.get('user_id')
    doctor = Users.objects.get(id=doctor_id)

    # Get hospital name based on admin's branch_id
    hospital_name = "Unknown Hospital"
    if doctor.branch:
        branch = HospitalBranches.objects.get(branch_code=doctor.branch.branch_code)
        hospital_name = branch.branch_name  # Fetch the hospital name
        hospital_branch = branch.branch_code
        try:
            doctor_val = Doctors.objects.get(email=user_email)
        except Patients.DoesNotExist:
            doctor_val = None
        
    return render(request,"myProfileDoctor.html", {'branch_name': hospital_name, 'branch_code': hospital_branch, 'doctor': doctor_val})
    
def testCentreDB(request):
    return render(request, 'testCentreDB.html')    

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
                request.session['user_email'] = str(user.email)
                request.session.set_expiry(86400)
                
                
                request.session['is_authenticated'] = True
                

                role_redirects = {
                    'masteradmin': '/masterAdminDB/',
                    'doctor': '/myProfile-Doctor/',
                    'admin': '/adminDB/',
                    'patient': '/patientProfile/',
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



# Fetch the existing banner
def get_banner(request):
    try:
        banner = Banners.objects.first()  # Assuming only one record exists
        if banner:
            return JsonResponse({"id": str(banner.id), "banner_file": banner.banner_file.url})
        return JsonResponse({"error": "No banner found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

# Update the banner image
@csrf_exempt
def update_banner(request):
    if request.method == 'POST':
        try:
            banner = Banners.objects.first()  # Fetch the only banner
            if not banner:
                return JsonResponse({"error": "No banner found to update."}, status=404)

            if 'banner_file' in request.FILES:
                # Delete old file
                if banner.banner_file:
                    banner.banner_file.delete()

                # Save new file
                banner.banner_file.save(request.FILES['banner_file'].name, ContentFile(request.FILES['banner_file'].read()))
                banner.save()

                return JsonResponse({"success": True, "message": "Banner updated successfully!", "banner_file": banner.banner_file.url})

            return JsonResponse({"error": "No file uploaded."}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


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
                    email=email,
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
        departments = Departments.objects.all().values('id', 'name', 'description', 'branch_id')
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
def edit_department(request, department_id):
    if request.method == "POST":
        try:
            department = Departments.objects.get(id=department_id)
            data = json.loads(request.body.decode("utf-8"))

            department.name = data.get("name", department.name)
            department.description = data.get("description", department.description)
            department.save()

            return JsonResponse({"success": True, "message": "Department updated successfully!"}, status=200)

        except Departments.DoesNotExist:
            return JsonResponse({"error": "Department not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# Delete Department
@csrf_exempt
def delete_department(request, department_id):
    if request.method == "DELETE":
        try:
            department = Departments.objects.get(id=department_id)
            department.delete()
            return JsonResponse({"success": True, "message": "Department deleted successfully!"}, status=200)
        except Departments.DoesNotExist:
            return JsonResponse({"error": "Department not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



# Get All Users (Receptionists & Doctors)
def get_users(request):
    receptionists = Users.objects.filter(role="Reception").values("id", "name", "email", "branch")
    doctors = Doctors.objects.select_related("user", "department").values("id", "name", "email", "department", "nmc_registration", "branch", "achievements", "education", "hospitals_worked", "expertise")

    return JsonResponse({"receptionists": list(receptionists), "doctors": list(doctors)}, status=200)




# Edit Doctor
@csrf_exempt
def edit_doctor(request, doctor_id):
    if request.method == 'POST':
        try:
            doctor = Doctors.objects.get(id=doctor_id)
            data = json.loads(request.body.decode("utf-8"))

            doctor.achievements = data.get("achievements", doctor.achievements)
            doctor.education = data.get("education", doctor.education)
            doctor.expertise = data.get("expertise", doctor.expertise)
            doctor.hospitals_worked = data.get("hospitals_worked", doctor.hospitals_worked)
            doctor.save()

            return JsonResponse({"success": True, "message": "Doctor updated successfully!"}, status=200)
        except Doctors.DoesNotExist:
            return JsonResponse({"error": "Doctor not found."}, status=404)

# Delete Receptionist
@csrf_exempt
def delete_user(request, user_id):
    if request.method == 'DELETE':
        try:
            user = Users.objects.get(id=user_id)
            user.delete()
            return JsonResponse({"success": True, "message": "Receptionist deleted successfully!"}, status=200)
        except Users.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)

# Delete the doctor
@csrf_exempt
def delete_doctor(request, doctor_id):
    if request.method == 'DELETE':
        try:
            # Find doctor in Doctors table
            doctor = Doctors.objects.get(id=doctor_id)
            user_email = doctor.email  # Get doctor's email before deleting
            print(user_email)

            # Delete doctor from Doctors table
            doctor.delete()

            # Delete user from Users table using email
            Users.objects.filter(email=user_email).delete()

            return JsonResponse({"success": True, "message": "Doctor deleted successfully from both tables!"}, status=200)

        except Doctors.DoesNotExist:
            return JsonResponse({"error": "Doctor not found."}, status=404)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        
        
# Adding health packages
@csrf_exempt
def add_health_package(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            branch_id = request.POST.get('branch_id')
            image = request.FILES.get('image')  # Handling the image file

            # Validate required fields
            if not name or not price or not branch_id:
                return JsonResponse({'error': 'Name, Price, and Branch ID are required!'}, status=400)

            
                        # Ensure the branch exists
            try:
                branch = HospitalBranches.objects.get(branch_code=branch_id)
            except HospitalBranches.DoesNotExist:
                return JsonResponse({'error': 'Invalid branch ID'}, status=400)
            
            # Create Health Package
            health_package = HealthPackages.objects.create(
                name=name,
                description=description,
                price=price,
                branch=branch,
                image=image  # Save the image file
            )

            return JsonResponse({'message': 'Health Package added successfully!', 'package_id': health_package.id}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


# Get All Health Packages
def get_health_packages(request):
    try:
        packages = HealthPackages.objects.all().values("id", "name", "description", "price", "branch_id", "image")
        return JsonResponse({"packages": list(packages)}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# Edit Health Package
@csrf_exempt
def edit_health_package(request, package_id):
    if request.method == "POST":
        try:
            package = HealthPackages.objects.get(id=package_id)
            name = request.POST.get("name")
            description = request.POST.get("description")
            price = request.POST.get("price")
            image = request.FILES.get("image")

            # Validate input
            if not name or not description or not price:
                return JsonResponse({"error": "Name, Description and Price are required!"}, status=400)

            # Update fields
            package.name = name
            package.description = description
            package.price = price

            # Update image if new image is uploaded
            if image:
                package.image = image

            package.save()
            return JsonResponse({"success": True, "message": "Health Package updated successfully!"}, status=200)

        except HealthPackages.DoesNotExist:
            return JsonResponse({"error": "Health Package not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# Delete Health Package
@csrf_exempt
def delete_health_package(request, package_id):
    if request.method == "DELETE":
        try:
            package = HealthPackages.objects.get(id=package_id)
            package.delete()
            return JsonResponse({"success": True, "message": "Health Package deleted successfully!"}, status=200)
        except HealthPackages.DoesNotExist:
            return JsonResponse({"error": "Health Package not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)



# Test Centre
# Create Test Centre (Stores in TestCentre & Users)
@csrf_exempt
def create_test_centre(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                data = request.POST
                name = data.get("name")
                description = data.get("description")
                price = data.get("price")
                branch_code = data.get("branch_code")  # Branch Foreign Key
                email = data.get("email")
                password = data.get("password")
                image = request.FILES.get('image')

                # Validate required fields
                if not all([name, description,branch_code, email, password, price, image]):
                    return JsonResponse({"error": "All fields are required!"}, status=400)

                # Check if branch exists
                try:
                    branch = HospitalBranches.objects.get(branch_code=branch_code)
                except HospitalBranches.DoesNotExist:
                    return JsonResponse({"error": "Invalid branch ID"}, status=400)

                # Create User
                user = Users.objects.create(
                    name=name,
                    email=email,
                    password=make_password(password),
                    role="TestCentre",
                    branch=branch,
                    is_active=True
                )

                # Create Test Centre
                test_centre = TestCentre.objects.create(
                    name=name,
                    email=email,
                    description=description,
                    price=price,
                    branch=branch,
                    testcentre_pic=image
                )

                return JsonResponse({"success": True, "message": "Test Centre added successfully!"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# Get All Test Centres
def get_test_centres(request):
    try:
        test_centres = TestCentre.objects.all().values('id', 'name', 'description', 'price', 'branch_id')
        return JsonResponse({"test_centres": list(test_centres)}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



# Edit Test Centre
@csrf_exempt
def edit_test_centre(request, test_centre_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            description = data.get("description")
            price = data.get("price")

            # Get Test Centre
            test_centre = TestCentre.objects.get(id=test_centre_id)
            if name:
                test_centre.name = name
            if description:
                test_centre.description = description
            if price:
                test_centre.price = price

            test_centre.save()
            return JsonResponse({"success": True, "message": "Test Centre updated successfully!"}, status=200)

        except TestCentre.DoesNotExist:
            return JsonResponse({"error": "Test Centre not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# Delete Test Centre (Deletes from Users & TestCentre)
@csrf_exempt
def delete_test_centre(request, test_centre_id):
    if request.method == "DELETE":
        try:
            test_centre = TestCentre.objects.get(id=test_centre_id)

            test_centre.delete()
            return JsonResponse({"success": True, "message": "Test Centre deleted successfully!"}, status=200)

        except TestCentre.DoesNotExist:
            return JsonResponse({"error": "Test Centre not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



###### Reception Functionalities ###############
# Add New Patient
@csrf_exempt
def add_patient(request):
    if request.method == "POST":
        data = request.POST
        print(data)
        try:
            data = request.POST
            pswd = data["password"]
            receiver_email = data["email"]
            dob = parse_date(data["dob"])  # Convert string to DateField format
            if not dob:
                return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

            # Auto-generate patient number
            current_year = datetime.datetime.now().year
            last_patient = Patients.objects.filter(patient_no__startswith=str(current_year)).order_by("-created_at").first()
            if last_patient:
                last_patient_no = int(last_patient.patient_no[-6:])  # Extract last 6 digits
                new_patient_no = f"{current_year}{last_patient_no + 1:06d}"
            else:
                new_patient_no = f"{current_year}000001"

            branch = HospitalBranches.objects.get(branch_code=data["branch_id"])
            department = Departments.objects.get(name=data["department_id"])
            
            doctor_ids = json.loads(data["doctors"])  # Convert JSON string to list
            assigned_doctors = []
            for doc_id in doctor_ids:
                doctor = Doctors.objects.get(id=doc_id)  # Fetch doctor by ID
                assigned_doctors.append({"email": doctor.email, "name": doctor.name})  # Store required fields


            # Transaction ensures data integrity across both tables
            with transaction.atomic():
                user = Users.objects.create(
                    name=data["name"],
                    email=data["email"],
                    password=make_password(data["password"]),
                    role="Patient",
                    branch=branch,
                    is_active=True,
                    profile_pic="profile_pics/patientPics.png"
                )

                patient = Patients.objects.create(
                    # user=user,
                    patient_no=new_patient_no,
                    name=data["name"],
                    email=data["email"],
                    age=data["age"],
                    dob=dob,
                    gender=data["gender"],
                    address=data["address"],
                    health_issues=data["health_issues"],
                    branch=branch,
                    assigned_doctors=json.dumps(assigned_doctors)
                )
                subject = "Welcome to syncHealth Digital"
                message = f"Your account has been created. Your initial password is: {pswd} | for email: {receiver_email}. Please reset it as soon as possible."
                email_from = settings.EMAIL_HOST_USER
                receipent_list = [receiver_email]
                send_mail(subject, strip_tags(message), email_from, receipent_list)
                


            return JsonResponse({"success": True, "message": "Patient added successfully."}, status=201)

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# Get Doctors for Dropdown
def get_doctors_by_department(request, department_name, branch_id):
    doctors = Doctors.objects.filter(department=department_name, branch=branch_id)
    doctor_list = [{"id": doc.id, "name": doc.name, "email": doc.email} for doc in doctors]
    return JsonResponse(doctor_list, safe=False)

# Get All Patients for Table Display
def get_patients(request):
    # patients = Patients.objects.select_related("branch").all()
    patients = Patients.objects.all()
    data = []
    
    for patient in patients:
        #  Parse assigned_doctors JSON safely
        print(patient.branch)
        try:
            assigned_doctors = json.loads(patient.assigned_doctors) if patient.assigned_doctors else []
        except json.JSONDecodeError:
            assigned_doctors = []
     

        data.append({
            "id": str(patient.id),
            "patient_no": patient.patient_no,
            "name": patient.name,
            "email":patient.email,
            "branch_name": f"{patient.branch}",
            "age": patient.age,
            "gender": patient.gender,
            "address": patient.address,
            "health_issues":patient.health_issues,
            "assigned_doctors": assigned_doctors
        })
    return JsonResponse(data, safe=False)



@csrf_exempt
def edit_patient(request, patient_id):
    if request.method == 'POST':
        try:
            # Get existing patient
            patient = Patients.objects.get(id=patient_id)

            # Parse request data
            data = json.loads(request.body.decode("utf-8"))
            new_address = data.get("address")
            new_health_issue = data.get("health_issue")
            new_doctors = data.get("assigned_doctors", [])

            # Update address
            if new_address:
                patient.address = new_address

            # Append new health issue (if any)
            if new_health_issue:
                existing_issues = patient.health_issues.split(", ") if patient.health_issues else []
                if new_health_issue not in existing_issues:
                    existing_issues.append(new_health_issue)
                    patient.health_issues = ", ".join(existing_issues)  # Save back to DB

            # Append new doctors while keeping existing ones
            try:
                assigned_doctors = json.loads(patient.assigned_doctors) if patient.assigned_doctors else []
            except json.JSONDecodeError:
                assigned_doctors = []
            print(assigned_doctors)

            # Ensure new doctors are not already assigned
            for new_doc in new_doctors:
                if not any(doc['email'] == new_doc['email'] for doc in assigned_doctors):
                    assigned_doctors.append(new_doc)  # Append only if not duplicate

            patient.assigned_doctors = json.dumps(assigned_doctors)  # Convert list to JSON string

            # Save updates
            patient.save()
            return JsonResponse({"success": True, "message": "Patient updated successfully.", "assigned_doctors": assigned_doctors}, status=200)

        except Patients.DoesNotExist:
            return JsonResponse({"error": "Patient not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# Delete Patient
@csrf_exempt
def delete_patient(request, patient_email):
    if request.method == 'DELETE':
        try:
            user = Users.objects.filter(email=patient_email).first()
            patient = Patients.objects.filter(email=patient_email).first()
            
            if user:
                user.delete()  # Delete user from Users table
                
            if patient:
                patient.delete()
                
            return JsonResponse({"success": True, "message": "Patient login credentials deleted."}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)




##### Doctor's setting available time

@csrf_exempt
def get_doctor_schedule(request, doctor_email):
    
    doctor_email = doctor_email  # Fetch logged-in doctor
    today = datetime.today().date()
    next_week = [today  + timedelta(days=i+1) for i in range(7)]

    schedule = []
    for day in next_week:
        record, created = DoctorAvailability.objects.get_or_create(
            doctor_id=doctor_email, date=day,
            defaults={"working_day_type": "None"}  # Default to None if not set
        )
        
        if created:
            record.save()

        is_locked = Appointments.objects.filter(doctor=record, status="Approved").exists()
        if is_locked:
            record.is_locked = True
            record.save()
        
        has_emergency = Appointments.objects.filter(doctor=record, status="Approved", is_emergency=True).exists()
        if has_emergency:
            record.is_locked = True  # Lock if emergency is booked
            record.save()

        schedule.append({
            "date": record.date.strftime("%Y-%m-%d"),
            "day":record.date.strftime("%A"),
            "working_day_type": record.working_day_type,
            "start_time": record.start_time.strftime("%H:%M") if record.start_time else None,
            "end_time": record.end_time.strftime("%H:%M") if record.end_time else None,
            "break_start": record.break_start.strftime("%H:%M") if record.break_start else None,
            "break_end": record.break_end.strftime("%H:%M") if record.break_end else None,
            "is_locked": record.is_locked,
            "emergency_available": record.emergency_available,
        })

    return JsonResponse({"schedule": schedule}, status=200)


@csrf_exempt
def update_doctor_schedule(request, doctor_email):
    if request.method == "POST":
        data = json.loads(request.body)
        doctor = doctor_email
        for entry in data["schedule"]:
            date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            availability = DoctorAvailability.objects.get(doctor=doctor, date=date)

            if availability.is_locked:
                continue  # Cannot modify locked days

            availability.working_day_type = entry["working_day_type"]
            availability.emergency_available = entry["emergency_available"]
            availability.save()  # Auto-assigns times based on type

        return JsonResponse({"message": "Schedule updated successfully!"}, status=200)
    return JsonResponse({"error": "Invalid request"}, status=400)



def doc_profile(request, doctor_email):
    if not request.session.get("is_authenticated"):
        logged_in = False
        msg = "You are not logged in!"
    
    if request.session.get('user_role')!='patient':
        logged_in = False
        msg = "You are not logged in as Patient!"
    else:
        logged_in = True
        msg = "You are logged in as patient!"
    
    user_email = request.session.get('user_email')
    try:
        patient_id = request.session.get('user_id')
        patient = Users.objects.get(id=patient_id)
    except:
        patient_id = None
        patient = None
    
    hospital_name = "Unknown Hospital"
    try:
        if patient.branch:
            branch = HospitalBranches.objects.get(branch_code=patient.branch.branch_code)
            hospital_name = branch.branch_name # Fetch the hospital name
            hospital_branch = branch.branch_code
    except:
        hospital_branch = None
    try:
        patient_val = Patients.objects.get(email=user_email)
    except Patients.DoesNotExist:
        patient_val = None
        
        
        
    doctor = get_object_or_404(Doctors, email=doctor_email)
    hospital_name = get_object_or_404(HospitalBranches, branch_code=doctor.branch_id)
    return render(request, 'docProfile.html',{'doc': doctor, 'hospital': hospital_name, "logged_in": logged_in, "msg":msg, 'branch_name': hospital_name, 'branch_code': hospital_branch, 'patients': patient_val})



def generate_time_slots(start_time, end_time, break_start, break_end, interval=20):
    if start_time is None or end_time is None:
        return [] 
    slots = []
    current_time = start_time

    while current_time < end_time:
        if break_start and break_end and break_start <= current_time < break_end:
            current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=interval)).time()
            continue  # Skip break time

        slots.append(current_time.strftime("%H:%M"))
        current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=interval)).time()

    return slots


def get_doctor_availability(request, doctor_email):
    """ Fetches 7-day availability with generated time slots """
    doctor = get_object_or_404(Doctors, email=doctor_email)
    print()
    today = date.today()
    
    # FIX: Use `filter()` instead of `get()` to handle multiple objects
    availability_records = DoctorAvailability.objects.filter(doctor=doctor.email, date__gte=today, date__lte=today + timedelta(days=7))

    data = []
    day_name = date.today()

    for avail in availability_records:
        slots = generate_time_slots(avail.start_time, avail.end_time, avail.break_start, avail.break_end)
        booked_slots = Appointments.objects.filter(doctor=avail, appointment_date=avail.date).values_list('appointment_time', flat=True)
        available_slots = [slot for slot in slots if slot not in booked_slots]
        day_name += timedelta(days=1)

        data.append({
            "date": avail.date.strftime("%Y-%m-%d"),
            "day":day_name.strftime("%A"),
            "available_time": available_slots,
            "on_leave": avail.start_time is None or avail.end_time is None  # Check if doctor is on leave
        })

    return JsonResponse(data, safe=False)

@api_view(["POST"])
def book_appointment(request):
    data = request.data
    patient = request.session.get('user_email')
    doctor_email = data.get("doctor_email")
    appointment_date = parse_date(data.get("appointment_date"))
    appointment_time = data.get("appointment_time")
    print(patient)
    
    doctor = get_object_or_404(Doctors, email=doctor_email)

    doctor = get_object_or_404(Doctors, email=doctor_email)
    branch_code = doctor.branch_id
    
    if Appointments.objects.filter(patient=patient, doctor=doctor_email, appointment_date=appointment_date).exists():
        return JsonResponse({"error": "You have already booked an appointment with this doctor on this day."}, status=400)
    
    

    if Appointments.objects.filter(doctor=doctor.email, appointment_date=appointment_date, appointment_time=appointment_time).exists():
        return JsonResponse({"error": "Slot already booked!"}, status=400)

    appointment = Appointments.objects.create(
        patient=patient,
        doctor=doctor_email,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        branch = branch_code,
        is_booked=True
    )
    subject = f"Appointment booked on {appointment_date} - {appointment_time}"
    message = f"""Your have booked an appointment on {appointment_date} at {appointment_time} with Dr. {doctor.name}({doctor_email}). This is just your booking you will be notified again about the appointment conformation.\n\nThank You!!\n\n\n\n-{doctor.branch}"""
    email_from = settings.EMAIL_HOST_USER
    receipent_list = [patient]
    send_mail(subject, strip_tags(message), email_from, receipent_list)
    

    return JsonResponse({"message": "Appointment booked successfully!", "appointment_id": str(appointment.id)})

    
    

@csrf_exempt
def submit_review(request, doctor_email):

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            patient_email = request.session.get('user_email')
            rating = data.get("rating")
            review_text = data.get("review", "")

            if not all([patient_email, doctor_email, rating]):
                return JsonResponse({"error": "Missing required fields."}, status=400)

            patient = Patients.objects.get(email=patient_email)
            
            existing_review = Reviews.objects.filter(doctor=doctor_email, patient=patient_email).first()

            if existing_review:
                # Update existing review
                existing_review.rating = rating
                existing_review.review = review_text
                existing_review.save()
                
            else:
                Reviews.objects.create(
                    doctor=doctor_email,
                    patient=patient,
                    rating=rating,
                    review=review_text,
                )

            # Update doctor's average rating & count
            rating_data = Reviews.objects.filter(doctor=doctor_email).aggregate(
                avg_rating=Avg("rating"), total_reviews=Count("id")
            )
            Doctors.objects.filter(email=doctor_email).update(
                rating=rating_data["avg_rating"], rating_counts=rating_data["total_reviews"]
            )

            return JsonResponse({"success": True, "message": "Review submitted successfully!"}, status=201)

        except Patients.DoesNotExist:
            return JsonResponse({"error": "Patient not found."}, status=404)
        except Users.DoesNotExist:
            return JsonResponse({"error": "Doctor not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def get_doctor_appointments(request):
    doctor_email = request.session.get('user_email')
    appointments = Appointments.objects.filter(doctor=doctor_email)

    data = [
        {
            "id": appointment.id,
            "patient_email": appointment.patient,
            "appointment_date": appointment.appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": appointment.appointment_time.strftime("%H:%M"),
            "appointment_status": appointment.status,
            "is_emergency": appointment.is_emergency,
        }
        for appointment in appointments
    ]
    return JsonResponse({"appointments": data}, status=200)


# Accept or Reject Appointment
@csrf_exempt
def manage_appointment_request(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            appointment_id = data.get("appointment_id")
            action = data.get("action")  # "Accept" or "Reject"
            rejection_reason = data.get("rejection_reason", "")

            appointment = get_object_or_404(Appointments, id=appointment_id, doctor=request.session.get('user_email'))
            doc = get_object_or_404(Doctors, email=request.session.get('user_email'))


            if action == "Accept":
                appointment.status = "Approved"
                appointment.save()
                send_mail(
                    subject="Appointment Confirmed",
                    message=f"Dear Patient User,\n\nYour appointment on {appointment.appointment_date} at {appointment.appointment_time} with Dr. {doc.name}({doc.email} | {doc.department}) has been confirmed.\n\nThank you.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[appointment.patient],
                )
                
                DoctorAvailability.objects.filter(doctor=request.session.get('user_email'), date = appointment.appointment_date).update(is_locked = True)

                return JsonResponse({"success": True, "message": "Appointment approved successfully."})

            elif action == "Reject":
                appointment.status = "Rejected"
                appointment.save()

                # Send rejection email
                send_mail(
                    subject="Appointment Rejected",
                    message=f"Dear Patient User,\n\nYour appointment on {appointment.appointment_date} at {appointment.appointment_time} with Dr. {doc.name}({doc.email}) has been rejected.\n\nReason: {rejection_reason}\n\nThank you.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[appointment.patient],
                )
                

                return JsonResponse({"success": True, "message": "Appointment rejected and email sent to patient."})

            else:
                return JsonResponse({"error": "Invalid action"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)





@csrf_exempt
def update_appointment_status(request):
    if request.method == "POST":
        data = json.loads(request.body)
        appointment = get_object_or_404(Appointments, id=data["appointment_id"])
        status = data["status"]
        doc = get_object_or_404(Doctors, email=appointment.doctor)
        print(doc.name)
        patient = get_object_or_404(Patients, email=appointment.patient)
        print(patient.name)
        
        if status == "Completed":
            appointment.status = status
            appointment.save()
            
            
            # Mail to Ptient
            send_mail(
                    subject="Appointment Consultation completed",
                    message=f"Dear {patient.name},\n\nYour appointment on {appointment.appointment_date} at {appointment.appointment_time} with Dr. {doc.name}({doc.email} | {doc.department}) has been Completed. You can now view your Prescription records digitally on your syncHealth profile.\n\nThank you for syncing with syncHealth.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[appointment.patient],
                )
            
            return JsonResponse({"message": f"Appointment marked as {status}!"}, status=200)
        
        if status == "Cancelled":
            appointment.status = status
            appointment.save()
            
            send_mail(
                    subject="Appointment Consultation Cancelled",
                    message=f"Dear {patient.name},\n\nYour appointment on {appointment.appointment_date} at {appointment.appointment_time} with Dr. {doc.name}({doc.email} | {doc.department}) has been cancelled because of your absence on the date: {appointment.appointment_date}.\n\nThank you.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[appointment.patient],
                )
            
            return JsonResponse({"message": f"Appointment marked as {status}!"}, status=200)


    return JsonResponse({"error": "Invalid request"}, status=400)



def get_prescription(request, appointment_id):
    try:
        appointment = Appointments.objects.get(id=appointment_id)
        # prescription = Prescriptions.objects.filter(patient=appointment.patient, doctor=appointment.doctor, date=appointment.appointment_date).first()
        prescription = Prescriptions.objects.filter(appointment_id=appointment.id).first()
        patient = get_object_or_404(Patients, email=appointment.patient)

        if prescription:
            return JsonResponse({"prescription": {
                "id": str(prescription.id),
                "blood_pressure_sys": prescription.pressure_systolic,
                "blood_pressure_dias": prescription.pressure_diastolic,
                "diabetes": prescription.diabetes,
                "medication": prescription.medication,
                "notes": prescription.notes,
                "date": appointment.appointment_date,
                "time": appointment.appointment_time,
                "patient_name": patient.name,
                "patient_email": patient.email
            }})
        else:
            return JsonResponse({"prescription": None})
    
    except Appointments.DoesNotExist:
        return JsonResponse({"error": "Appointment not found"}, status=404)





@csrf_exempt
def save_prescription(request):
    if request.method == "POST":
        data = json.loads(request.body)

        appointment = Appointments.objects.get(id=data['appointment_id'])
        prescription, created = Prescriptions.objects.update_or_create(
            
            patient=appointment.patient,
            doctor=appointment.doctor,
            date=appointment.appointment_date,
            defaults={
                "appointment_id" : data.get("appointment_id", ""),
                "pressure_systolic": data.get("blood_pressure_systolic", ""),
                "pressure_diastolic": data.get("blood_pressure_diastolic", ""),
                "diabetes": data.get("diabetes", ""),
                "medication": data.get("medication", ""),
                "notes": data.get("notes", ""),
            }
        )

        return JsonResponse({"message": "Prescription saved successfully!"})
    
    return JsonResponse({"error": "Invalid request"}, status=400)






@csrf_exempt
def manage_prescription(request):
    if request.method == "POST":
        data = json.loads(request.body)
        doctor = get_object_or_404(Doctors, email=data["doctor_email"])
        patient = get_object_or_404(Patients, email=data["patient_email"])
        prescription, created = Prescriptions.objects.get_or_create(
            doctor=doctor, patient=patient, date=data["date"]
        )

        prescription.blood_pressure = data.get("blood_pressure", prescription.blood_pressure)
        prescription.diabetes = data.get("diabetes", prescription.diabetes)
        prescription.medication = data.get("medication", prescription.medication)
        prescription.notes = data.get("notes", prescription.notes)
        prescription.save()

        return JsonResponse({"message": "Prescription saved successfully!"}, status=200)
    
    return JsonResponse({"error": "Invalid request"}, status=400)







################### Test Centre #########################
def test_centres(request, centre_email):
    
    user_role =  request.session.get('user_role')
    
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    
    tc = get_object_or_404(TestCentre, email=centre_email)
    
    profile = get_object_or_404(Users, email=centre_email)
    profile_pic = profile.profile_pic
    
    return render(request, 'testCentre.html',{'tst_cnt': tc, 'tst_profile':profile_pic, 'user_email':user_email, 'user_role':user_role})   




@csrf_exempt
def book_test(request):
    """Handles test booking requests."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            patient = data.get("patient")
            test_centre = data.get("test_centre")
            booking_date = data.get("booking_date")

            # Validate inputs
            if not all([patient, test_centre, booking_date]):
                return JsonResponse({"error": "All fields are required."}, status=400)

            booking_date = parse_date(booking_date)
            if not booking_date or booking_date < datetime.today().date():
                return JsonResponse({"error": "Invalid booking date."}, status=400)

            test_centre = get_object_or_404(TestCentre, email=test_centre)
            patient = get_object_or_404(Patients, email=patient)
            
            existing_booking = TestBooking.objects.filter(
                patient=patient.email,
                test_department=test_centre.email,
                booking_date=booking_date
            ).exists()

            if existing_booking:
                return JsonResponse({"error": "You already have a booking at this test centre on this date."}, status=400)


            # Check if 50 bookings already exist for that test centre on the selected date
            booking_count = TestBooking.objects.filter(test_department=test_centre, booking_date=booking_date).count()
            if booking_count >= 50:
                return JsonResponse({"error": "Booking limit reached for this day."}, status=400)

            # Create booking
            booking = TestBooking.objects.create(
                patient=patient.email,
                status="Pending",
                test_department=test_centre.email,
                booking_date=booking_date,
            )
            return JsonResponse({"message": "Test booked successfully!", "booking_id": str(booking.id)})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid data format."}, status=400)

    return JsonResponse({"error": "Invalid request."}, status=405)







############################ Health Packages #######################
def health_packages(request, package_id):
    
    
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    
    hp = get_object_or_404(HealthPackages, id=package_id)

    
    return render(request, 'healthPackage.html',{'hlt_pkg': hp, 'user_email':user_email, 'user_role':user_role})   



@csrf_exempt
def book_health_package(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            patient_email = data.get("patient_email")
            test_id = data.get("test_id")
            branch = data.get("branch")
            test_date = data.get("test_date")

            if not all([patient_email, test_id, branch, test_date]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # Validate date
            try:
                test_date_obj = datetime.strptime(test_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"error": "Invalid date format"}, status=400)

            # Get user and package
            try:
                patient = Users.objects.get(email=patient_email)
            except Users.DoesNotExist:
                return JsonResponse({"error": "Invalid patient email"}, status=404)

            try:
                health_package = HealthPackages.objects.get(id=test_id)
            except HealthPackages.DoesNotExist:
                return JsonResponse({"error": "Invalid package ID"}, status=404)

            # Check if patient already booked this package on the same date
            if HealthPackageBookings.objects.filter(patient=patient.email, test_date=test_date_obj).exists():
                return JsonResponse({"error": "You already booked this package on this date."}, status=400)

            # Limit 20 bookings per day
            if HealthPackageBookings.objects.filter(test=health_package, test_date=test_date_obj).count() >= 20:
                return JsonResponse({"error": "Booking limit reached for this package on the selected date."}, status=400)

            # Create booking
            booking = HealthPackageBookings.objects.create(
                test=health_package, patient=patient.email, branch=branch, test_date=test_date_obj, status="Pending"
            )

            return JsonResponse({"message": "Booking successful!", "booking_id": str(booking.id)})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


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