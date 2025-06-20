import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.managers import UserManager


#-------- User ---------#


AUTH_PROVIDERS ={'email':'email', 'google':'google'}

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        max_length=255, verbose_name=_("Email Address"), unique=True
    )
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=100, verbose_name=_("Last Name"))
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified=models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    auth_provider=models.CharField(max_length=50, blank=False, null=False, default=AUTH_PROVIDERS.get('email'))

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def tokens(self):    
        refresh = RefreshToken.for_user(self)
        return {
            "refresh":str(refresh),
            "access":str(refresh.access_token)
        }


    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name.title()} {self.last_name.title()}"
    
    
    
class UserProfile(models.Model):
    """Extended user profile model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    has_onboarded = models.BooleanField(default=False)
    verification_method_expertise = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"



#-------- Expertise ---------#

class ExpertiseArea(models.Model):
    """Subject areas or skills"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100) 
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        
        
class UserExpertise(models.Model):
    """Many-to-Many relationship between users and expertise areas with additional data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expertise')
    expertise = models.ForeignKey(ExpertiseArea, on_delete=models.CASCADE, related_name='experts')
    proficiency_level = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], default=3)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.expertise.name} (Level {self.proficiency_level})"
    
    class Meta:
        unique_together = ('user', 'expertise')
        ordering = ['-proficiency_level']



#-------- OTP models ---------#



class OneTimePassword(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    otp_hash=models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} - otp code"
    
    
class FailedPasswordReset(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField(null= True, blank = True)
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Failed attempt of password reset'
        verbose_name_plural = "Failed attempts of password resets"