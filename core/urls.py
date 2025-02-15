from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.home, name='home'),
    path('login/',views.login_view, name='loginPage'),
    path('api/login/', views.login_api, name='login_api'),
    path('logout/',views.logout_view, name='logout'),
    path('docProfile/', views.docProfile, name="docProfile"),
    path('patientProfile/', views.patientProfile, name='patientProfile'),
    path('adminDB/', views.adminDB, name='adminDB'),
    path('masterAdminDB/', views.masterAdmin, name='masterAdminDB'),
    path('receptionDB/', views.receptionDB, name='receptionistDB'),
    path('get_hospital_branches/', views.get_hospital_branches, name="get_hospital_branches"),
    path('get_admins/', views.get_admins, name="get_admins"),
    path('add_hospital_branch/', views.add_hospital_branch, name="add_hospital_branch"),
    path('add_admin/', views.add_admin, name="add_admin"),
    path('edit_hospital_branch/<uuid:branch_id>/', views.edit_hospital_branch, name="edit_hospital_branch"),
    path('edit_admin/<uuid:admin_id>/', views.edit_admin, name="edit_admin"),
    path('delete_hospital_branch/<uuid:branch_id>/', views.delete_hospital_branch, name="delete_hospital_branch"),
    path('delete_admin/<uuid:admin_id>/', views.delete_admin, name="delete_admin"),
    #path for admin tasks
    path('api/add-receptionist/', views.add_receptionist),
    path('api/add-doctor/', views.add_doctor, name="add-doctor"),
    path('api/add-department/', views.add_department, name="add-department"),
    path('api/get-users/', views.get_users),
    path('api/get-departments/', views.get_departments, name="get-departments"),
    path('api/edit-user/<uuid:user_id>/', views.edit_user),
    path('api/delete-user/<uuid:user_id>/', views.delete_user),
    path('api/edit-department/<uuid:dept_id>/', views.edit_department),
    path('api/delete-department/<uuid:dept_id>/', views.delete_department),
    # path('create-user/', create_user_view, name='create-user')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
