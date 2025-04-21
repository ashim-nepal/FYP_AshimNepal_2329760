from django.db import models
import uuid, json
from django.contrib.auth.hashers import make_password, check_password
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from datetime import time
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.html import strip_tags


@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:  # Send email only when a user is created
        subject = "Welcome to Our Service"
        message = f"Your account has been created. Your initial password is: {instance.password}. Please reset it as soon as possible."
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]

        send_mail(subject, strip_tags(message), email_from, recipient_list)

class HospitalBranches(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch_name = models.CharField(max_length=100)
    branch_location = models.CharField(max_length=255)
    branch_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.branch_name


class Users(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=255)
    last_login = models.DateTimeField(default=now)

    def save(self, *args, **kwargs):
        # Hash password only if it's not already hashed
        if not self.pk or not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    name = models.CharField(max_length=100)
    role = models.CharField(
    max_length=20, 
    choices=[
        ('Patient', 'Patient'),
        ('Doctor', 'Doctor'),
        ('Admin', 'Admin'),
        ('MasterAdmin', 'Master Admin'),
        ('Reception', 'Receptionist'),
        ('TestCentre', 'Test Centre')
    ]
    )
    branch = models.ForeignKey(HospitalBranches, to_field='branch_code',on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_email_field_name(self):
        return "email"
    
    def get_username(self):
        return self.email
    
    def __str__(self):
        return self.name


class Patients(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_no = models.CharField(max_length=20, unique=True, editable=False, blank=True)  # Unique Patient No
    name = models.CharField(max_length=100, default="Patients Name")
    dob = models.DateField(blank=True, null=True)
    age = models.IntegerField(default=0)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], default="Male")
    address = models.TextField(default="Patient's addredd")
    email = models.EmailField(unique=True, null=True, blank=True)
    branch = models.ForeignKey('HospitalBranches', to_field='branch_code', on_delete=models.CASCADE)  # FK to branch_code
    assigned_doctors = models.JSONField(default=dict, blank=True)  # Store {doc_id: doc_name} pairs
    health_issues = models.JSONField(default=list, blank=True)  # List of health issues

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Generate a unique Patient No (YY0000001 format)
        if not self.patient_no:
            year_prefix = now().strftime("%y")
            last_patient = Patients.objects.filter(patient_no__startswith=year_prefix).order_by('-patient_no').first()
            last_count = int(last_patient.patient_no[2:]) + 1 if last_patient else 1
            self.patient_no = f"{year_prefix}{str(last_count).zfill(7)}"

        # Auto-calculate Age
        self.age = now().year - self.dob.year
        super().save(*args, **kwargs)

    def assign_doctor(self, doctor_id, doctor_name, health_issue):
        """
        Assigns an additional doctor to the patient and adds a new health issue.
        """
        if doctor_id not in self.assigned_doctors:
            self.assigned_doctors[doctor_id] = doctor_name
        self.health_issues.append(health_issue)
        self.save()

    def get_assigned_doctor_names(self):
        """ Return a comma-separated list of assigned doctor names. """
        return ', '.join(self.assigned_doctors.values())

    def __str__(self):
        return f"{self.patient_no} - {self.name}"


class Departments(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(HospitalBranches,to_field='branch_code', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='department_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Doctors(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Doctor's Name")  # Doctor Name
    email = models.EmailField(unique=True, null=True, blank=True)
    department = models.TextField(default="No Departments added")
    nmc_registration = models.IntegerField(unique=True, null=True)  # Unique NMC Registration Number
    expertise = models.TextField(default="No expertise added")  # Expertise Field
    education = models.TextField(default="No Education added")  # Education Details
    hospitals_worked = models.TextField(default="syncHealth")  # List of Hospitals Previously Worked
    achievements = models.TextField(default="No achievements added")  # Achievements 
    rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.000)  # Rating (Updated from Reviews)
    rating_counts = models.IntegerField(default=0)
    branch = models.ForeignKey(HospitalBranches, to_field='branch_code', on_delete=models.CASCADE)  # Branch ForeignKey (Using branch_code)

    def calculate_rating(self):
        """Calculates average rating from the Reviews model."""
        from core.models import Reviews  # Import inside function to avoid circular imports
        reviews = Reviews.objects.filter(doctor=self)
        if reviews.exists():
            self.rating = sum(review.rating for review in reviews) / reviews.count()
        else:
            self.rating = 0.0
        self.save()

    def __str__(self):
        # return f"{self.name} - {self.department.name} -{self.rating}" 
        return f"{self.name} - {self.department} -{self.rating}" 


class DoctorAvailability(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(Users,to_field='email', on_delete=models.CASCADE)  # Doctor user
    date = models.DateField(null=True)
    working_day_type = models.CharField(
        max_length=20,
        choices=[("Full", "Full Day"),("Half_Morning", "Half Morning") ,("Half_Evening", "Half Evening"), ("Leave", "Leave")], default="Full"
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    emergency_start_time = models.TimeField(null=True, blank=True)
    emergency_stop_time = models.TimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    emergency_available = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Auto-assigns timings based on selected working type.
        if self.working_day_type == "Full":
            self.start_time, self.end_time = time(9, 0), time(17, 0)
            self.break_start, self.break_end = time(13, 30), time(14, 30)
        elif self.working_day_type == "Half_Morning":
            self.start_time, self.end_time = time(9, 0), time(13, 30)
            self.break_start, self.break_end = time(11, 30), time(12, 0)
        elif self.working_day_type == "Half_Evening":
            self.start_time, self.end_time = time(14, 0), time(17, 30)
            self.break_start, self.break_end = time(16, 0), time(16, 30)
        elif self.working_day_type == "Leave":
            self.start_time = self.end_time = self.break_start = self.break_end = None
        
        if self.emergency_available == True:
            self.emergency_start_time, self.emergency_stop_time = time(19, 0), time(20, 20)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.working_day_type})"


class Appointments(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.CharField(max_length=100, default="Patient's Email")
    doctor = models.CharField(max_length=100, default="Doctor's Email")
    branch = models.CharField(max_length=20, default="")
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    is_booked = models.BooleanField(default=False)  # If a patient has booked this slot
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Pending')
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.name} - {self.doctor.user.name}"





class GroupMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.CharField(max_length=255) 
    department_group = models.CharField(max_length=255) 
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.name} -> {self.department_group.department}"


class ChatGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.CharField(max_length=100)
    members = models.ManyToManyField(Users)  # Doctors only

    def __str__(self):
        return self.department


class Messages(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, blank=True, related_name='received_messages')
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat_uploads/", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.name} {'-> ' + self.receiver.name if self.receiver else '-> Group: ' + self.group.department}"


class HealthPackages(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    branch = models.ForeignKey(HospitalBranches,to_field='branch_code', on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='health_test_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class HealthPackageBookings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(HealthPackages, on_delete=models.CASCADE)
    patient = models.CharField(max_length=100, default="Patient's Email") 
    branch = models.CharField(max_length=100, default="Hospital branch") 
    test_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Approved', 'Approved'),('Processing', 'Processing'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Pending')
    report_file = models.FileField(upload_to='test_reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test.name} - {self.patient.user.name}"


class TestResults(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patients, on_delete=models.CASCADE)
    test = models.ForeignKey(HealthPackages, on_delete=models.CASCADE)
    report_file = models.FileField(upload_to='health_test_reports/', null=True, blank=True)
    result_value = models.FloatField()
    result_date = models.DateField()

    def __str__(self):
        return f"{self.test.name} - {self.patient.user.name}"


class TestCentre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)  # E.g., Blood Test, Urine Test, CT Scan
    email = models.EmailField(unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Cost of test
    testcentre_pic = models.ImageField(upload_to='testcentre_pics/', null=True, blank=True)
    branch = models.ForeignKey(HospitalBranches,to_field='branch_code', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.branch}"
    

class TestBooking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Sample Collected', 'Sample Collected'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Completion Notified', 'Completion Notified'),
        ('Cancelled', 'Cancelled'),
        ('Rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.CharField(max_length=100, default="Patient's Email")  # Linked Patient
    test_department = models.CharField(max_length=100, default="Department email") # Selected Test Department
    booking_date = models.DateField()  # Date of booking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  # Test Status
    test_report = models.FileField(upload_to="test_reports/", null=True, blank=True)  # Test Report PDF
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.test_department.name} ({self.status})"

class Prescriptions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment_id = models.CharField(max_length=80, null=True, blank=True)
    patient = models.CharField(max_length=50, null=True, blank=True)
    doctor = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateField()
    pressure_systolic = models.CharField(max_length=20, null=True, blank=True) # Top mm/Hg
    pressure_diastolic = models.CharField(max_length=20, null=True, blank=True) # Top mm/Hg
    diabetes = models.CharField(max_length=20, null=True, blank=True) # mg/dL
    medication = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.name} - {self.doctor.user.name}"


class Reviews(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.CharField(max_length=100, null=True)
    patient = models.ForeignKey(Patients,to_field="email", on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} -> {self.doctor}"


class Banners(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    banner_name = models.CharField(max_length=50)
    banner_file = models.ImageField(upload_to='banners/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.banner_name


class Payments(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    booking = models.ForeignKey(HealthPackageBookings, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')], default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=[('Credit Card', 'Credit Card'), ('PayPal', 'PayPal'), ('Stripe', 'Stripe')])

    def __str__(self):
        return f"{self.user.name} - {self.amount}"


class WorkflowAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(HospitalBranches, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    age_group = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    health_issue = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analytics - {self.user.name}"

