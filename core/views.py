from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "home.html")

def docProfile(request):
    return render(request, "docProfile.html")

def patientProfile(request):
    return render(request,"patientProfile.html")