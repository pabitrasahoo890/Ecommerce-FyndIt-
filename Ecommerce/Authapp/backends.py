from django.contrib.auth.backends import BaseBackend
from .models import CustomUser

class PhoneNumberBackend(BaseBackend):
    """Custom authentication backend to login users using phone number"""

    def authenticate(self, request, username=None, **kwargs):
        try:
            return CustomUser.objects.get(phone=username)
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
