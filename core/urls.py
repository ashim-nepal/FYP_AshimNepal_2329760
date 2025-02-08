from django.urls import path
from .views import home, HospitalBranchView, AdminView
from . import views



urlpatterns = [
    path('', home, name='home'),
    path('login/',views.login_view, name='loginPage'),
    path('api/login/', views.login_api, name='login_api'),
    path('docProfile/', views.docProfile, name="doctorProfile"),
    path('patientProfile/', views.patientProfile),
    path('adminDB/', views.adminDB),
    path('masterAdminDB/', views.masterAdmin, name='masterAdminDashboard'),
    path('masterAdminDB/api/hospitals/', HospitalBranchView.as_view(), name='hospital-list-create'),
    path('masterAdminDB/api/hospitals/<str:pk>/', HospitalBranchView.as_view(), name='hospital-detail-update-delete'),
    path('masterAdminDB/api/admins/', AdminView.as_view(), name='admin-list-create'),
    path('masterAdminDB/api/admins/<str:pk>/', AdminView.as_view(), name='admin-detail-update-delete'),
    path('receptionDB/', views.receptionDB, name='receptionistDashboard'),
    # path('create-user/', create_user_view, name='create-user')
]
