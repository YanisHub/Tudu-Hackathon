# Standard library imports
import re
import time

# Django imports
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str, smart_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

# Third-party imports
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

# Local imports
from .models import (
    FailedPasswordReset,
    User,
    UserProfile,
    UserExpertise,
    ExpertiseArea
)
from .utils import send_normal_email


#-------- User Serializers ---------#

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the main User model.

    Includes basic user details and potentially nested profile information.
    """

    # profile = UserProfileSerializer(read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "is_active",
            "is_staff",
            "date_joined",
            "profile",  # Include the nested profile or profile data
        ]
        read_only_fields = ["id", "email", "is_active", "is_staff", "date_joined"]

    def get_profile(self, obj):
        # Provides a simplified profile representation or key details
        # Avoids fetching the full profile unless necessary for this context
        try:
            profile = obj.profile
            return {
                "bio": profile.bio,
                "has_onboarded": profile.has_onboarded,
                "avatar": profile.avatar.url if profile.avatar else None,
            }
        except UserProfile.DoesNotExist:
            return None # Or return an empty dict {}

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=68, min_length=6, write_only=True)
    password2= serializers.CharField(max_length=68, min_length=6, write_only=True)

    class Meta:
        model=User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, attrs):
        password=attrs.get('password', '')
        password2 =attrs.get('password2', '')
        if password !=password2:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas")
        
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins une lettre majuscule")
        if not re.search(r'[0-9]', password):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins un chiffre")
        if not re.search(r'[!@#$%^&*()]', password):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins un caractère spécial")
        
        return attrs

    def create(self, validated_data):
        user= User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=validated_data.get('password')
            )
        
        # Créer un profil utilisateur pour chaque user registration
        UserProfile.objects.create(
            user=user,
            has_onboarded=False
        )
        
        return user

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=155, min_length=6)
    password=serializers.CharField(max_length=68, write_only=True)
    full_name=serializers.CharField(max_length=255, read_only=True)
    access_token=serializers.CharField(max_length=255, read_only=True)
    refresh_token=serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'access_token', 'refresh_token']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        request=self.context.get('request')
        user = authenticate(request, email=email, password=password)
        if not user:
            raise AuthenticationFailed("Identifiants invalides, veuillez réessayer")
        if not user.is_verified:
            raise AuthenticationFailed("L'email n'est pas vérifié")
        
        # Ensure the user ID is properly handled as a UUID string
        tokens=user.tokens()
        return {
            'email':user.email,
            'full_name':user.full_name,
            "access_token":str(tokens.get('access')),
            "refresh_token":str(tokens.get('refresh'))
        }

class LogoutUserSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

    default_error_message = {
        'bad_token': ('Le token est expiré ou invalide')
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return attrs

    def save(self, **kwargs):
        try:
            token=RefreshToken(self.token)
            token.blacklist()
            return True
        except TokenError:
            raise serializers.ValidationError({
                'refresh_token': self.default_error_messages['bad_token']
            })

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model.

    Handles serialization and deserialization of user profile data, including
    the user's biography, type, and onboarding status.
    """

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",  # Typically read-only or handled carefully
            "bio",
            "avatar",
            "has_onboarded",
            "verification_method_expertise",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        # Custom update logic can go here if needed
        # For example, handling nested updates or specific field logic
        instance.bio = validated_data.get("bio", instance.bio)
        # instance.user_type = validated_data.get("user_type", instance.user_type)
        instance.has_onboarded = validated_data.get(
            "has_onboarded", instance.has_onboarded
        )
        # Handle avatar update if provided
        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.save()
        return instance


#-------- Password Reset Serializers ---------#

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    
    class Meta:
        fields = ['email']

    def validate(self, attrs):
        email = attrs.get('email')
        email_exists = User.objects.filter(email=email).exists()

        if not email_exists:
            FailedPasswordReset.objects.create(
                email = email,
                ip_address = self.context['request'].META.get('REMOTE_ADDR', 'inconnue'),
            )
            time.sleep(0.5)
        else:
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            
            #### A changer en production ####
            frontend_url = settings.FRONTEND_URL
            abslink = f"{frontend_url}/password-reset-confirm/{uidb64}/{token}"
            email_body = f"Bonjour {user.first_name}, utilisez le lien suivant pour réinitialiser votre mot de passe : {abslink}"
            data = {
                'email_body': email_body, 
                'email_subject': "Réinitialisation de votre mot de passe", 
                'to_email': user.email
                }
            send_normal_email(data)

        return super().validate(attrs)

class SetNewPasswordSerializer(serializers.Serializer):
    password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password=serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64=serializers.CharField(min_length=1, write_only=True)
    token=serializers.CharField(min_length=3, write_only=True)

    class Meta:
        fields = ['password', 'confirm_password', 'uidb64', 'token']

    def validate(self, attrs):
        try:
            token=attrs.get('token')
            uidb64=attrs.get('uidb64')
            password=attrs.get('password')
            confirm_password=attrs.get('confirm_password')

            user_id=force_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("Le lien de réinitialisation est invalide ou a expiré", 401)
            if password != confirm_password:
                raise AuthenticationFailed("Les mots de passe ne correspondent pas")
            user.set_password(password)
            user.save()
            
            return attrs
        
        except Exception as e:
            raise AuthenticationFailed("Le lien est invalide ou a expiré")


#-------- Expertise Serializers ---------#
        
class ExpertiseAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertiseArea
        fields = ['id', 'name', 'parent', 'created_at']
        read_only_fields = ['id', 'created_at']
        
class UserExpertiseSerializer(serializers.ModelSerializer):
    expertise_details = ExpertiseAreaSerializer(source='expertise', read_only=True)
    
    class Meta:
        model = UserExpertise
        fields = ['id', 'expertise', 'expertise_details', 
                  'is_verified', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'created_at', 'updated_at']