from django.contrib.auth.backends import ModelBackend
from .models import Users

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
