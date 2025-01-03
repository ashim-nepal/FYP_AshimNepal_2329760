from django.urls import path
from .views import home
from . import views
urlpatterns = [
    path('', home, name='home'),
    path('docProfile/', views.docProfile),
    path('patientProfile/', views.patientProfile),
    path('adminDB/', views.adminDB),
    path('masterAdminDB/', views.masterAdmin),
]
