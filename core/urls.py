from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.home, name='home'),
    path('login/',views.login_view, name='loginPage'),
    path('api/login/', views.login_api, name='login_api'),
    path('logout/',views.logout_view, name='logout'),
    path('docProfile/<str:doctor_email>/', views.doc_profile, name="doc_profile"),
    path('patientProfile/', views.patientProfile, name='patientProfile'),
    path('viewPatientProfile/<str:patient_email>/',views.view_patientProfile, name='view_patientProfile'),
    path('adminDB/', views.adminDB, name='adminDB'),
    path('masterAdminDB/', views.masterAdmin, name='masterAdminDB'),
    path('receptionDB/', views.receptionDB, name='receptionistDB'),
    path('myProfile-Doctor/', views.doctorProfilePage, name="myProfile-Doctor"),
    path('testCentreDB/',views.testCentreDB, name="testCentreDB"),
    path('get_hospital_branches/', views.get_hospital_branches, name="get_hospital_branches"),
    path('get_admins/', views.get_admins, name="get_admins"),
    path('add_hospital_branch/', views.add_hospital_branch, name="add_hospital_branch"),
    path('add_admin/', views.add_admin, name="add_admin"),
    path('edit_hospital_branch/<uuid:branch_id>/', views.edit_hospital_branch, name="edit_hospital_branch"),
    path('edit_admin/<uuid:admin_id>/', views.edit_admin, name="edit_admin"),
    path('delete_hospital_branch/<uuid:branch_id>/', views.delete_hospital_branch, name="delete_hospital_branch"),
    path('delete_admin/<uuid:admin_id>/', views.delete_admin, name="delete_admin"),
    path("api/get-banner/", views.get_banner, name="get-banner"),
    path("api/update-banner/", views.update_banner, name="update-banner"),
    path("api/send-notice/", views.send_notice, name="send_notice"),
    #path for admin tasks
    path('api/add-receptionist/', views.add_receptionist),
    path('api/add-doctor/', views.add_doctor, name="add-doctor"),
    path('api/add-department/', views.add_department, name="add-department"),
    path('api/get-users/', views.get_users),
    path('api/get-departments/', views.get_departments, name="get-departments"),
    path('api/edit-user/<uuid:user_id>/', views.edit_user),
    path('api/delete-user/<uuid:user_id>/', views.delete_user),
    path('api/edit-department/<uuid:department_id>/', views.edit_department, name="edit_department"),
    path('api/delete-department/<uuid:department_id>/', views.delete_department, name="delete_department"),
    path('api/get-users/', views.get_users, name='get_users'),
    path('api/edit-doctor/<str:doctor_id>/', views.edit_doctor, name='edit_doctor'),
    path('api/delete-user/<str:user_id>/', views.delete_user, name='delete_user'),
    path('api/delete-doctor/<str:doctor_id>/', views.delete_doctor, name='delete_doctor'),
    path('api/add-health-package/', views.add_health_package, name='add_health_package'),
    path("api/get-health-packages/", views.get_health_packages, name="get_health_packages"),
    path("api/edit-health-package/<uuid:package_id>/", views.edit_health_package, name="edit_health_package"),
    path("api/delete-health-package/<uuid:package_id>/", views.delete_health_package, name="delete_health_package"),
    path("api/create-test-centre/", views.create_test_centre, name="create_test_centre"),
    path("api/get-test-centres/", views.get_test_centres, name="get_test_centres"),
    path("api/edit-test-centre/<uuid:test_centre_id>/", views.edit_test_centre, name="edit_test_centre"),
    path("api/delete-test-centre/<uuid:test_centre_id>/", views.delete_test_centre, name="delete_test_centre"),
    #path for reception task
    path("api/get-doctors/<str:department_name>/<str:branch_id>/", views.get_doctors_by_department, name="get_doctors_by_department"),
    path('api/add-patient/', views.add_patient, name='add_patient'),
    path('api/get-patients/', views.get_patients, name='get_patients'),
    path('api/edit-patient/<uuid:patient_id>/', views.edit_patient, name='edit_patient'),
    path('api/delete-patient/<str:patient_email>/', views.delete_patient, name='delete_patient'),
    # Doctor time availibality management
    path('api/get-doctor-schedule/<str:doctor_email>/', views.get_doctor_schedule, name="get-doctor-schedule"),
    path('api/update-doctor-schedule/<str:doctor_email>/', views.update_doctor_schedule, name = "update_doctor_schedule"),
    # Doctor schedules and appointment bookings
    path("api/get-weekly-slots/<str:doctor_email>/", views.get_doctor_availability, name="get_weekly_slots"),
    path("api/book-appointment/", views.book_appointment, name="book_appointment"),
    # Review doctor
    path("api/submit-review/<str:doctor_email>/", views.submit_review, name="submit_review"),
    # Doctor's tasks
    path("api/get-doctor-appointments/", views.get_doctor_appointments, name="get-doctor-appointments"),
    path("api/manage-appointment-request/", views.manage_appointment_request, name="manage-appointment-request"),
    path("api/update-appointment/", views.update_appointment_status, name="update_appointment"),
    path("api/update-appointment-status/", views.update_appointment_status, name="update_appointment_status"),
    # Doctor prescription task
    path('manage-prescription/', views.manage_prescription, name="manage_prescription"),
    path('get_prescription/<uuid:appointment_id>/', views.get_prescription, name='get_prescription'),
    path('save_prescription/', views.save_prescription, name='save_prescription'),
    # Test Centres
    path("test-centres/<str:centre_email>/", views.test_centres, name="test_centres"),
    path("api/book-test-appointment/", views.book_test, name="book_test"),
    path("api/get-tc-appointments/", views.get_tc_appointments, name="get_appointments"),
    path("api/update-tc-status/", views.update_tc_status, name="update_status"),
    path("api/reject-test-req/", views.reject_test_request, name="reject_test"),
    path("api/send-test-report/", views.send_test_report, name="send_report"),
    
    # Health Packages
    path("health-package/<uuid:package_id>/", views.health_packages, name="health_packages"),
    path('api/book-health-package/', views.book_health_package, name = "book_healthPackage"),
    # Reset PAssword and change password
    path("myAccPage/", views.myAccPage, name="myAccPage"),
    path("forgot-password/", views.forgotPass, name="forgotPassword"),
    path("reset-password/<uidb64>/<token>/", views.resetPass, name="resetPassword"),
    path("api/update-password/", views.update_password),
    path("api/send-reset-password/", views.send_reset_password),
    path("api/forgotten-reset-password/", views.reset_forgotten_password, name="reset_password_submit"),
    # PAtient vews graph and records
    path('api/prescriptions/<str:patient_email>/', views.prescriptions_view),
    path('api/patient-history/<str:patient_email>/', views.patient_history),
    path("api/patient-records/<str:patient_email>/", views.get_detailed_patient_records),
    
    
    # path('create-user/', create_user_view, name='create-user')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
