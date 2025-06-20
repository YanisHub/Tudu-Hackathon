import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from accounts.models import (
    User,
    UserProfile
)
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.db import transaction


class Google():
    @staticmethod
    def validate(access_token):
        try:
            id_info = id_token.verify_oauth2_token(access_token, google_requests.Request())
            if 'accounts.google.com' in id_info['iss']:
                return id_info
            else:
                raise ValidationError('Token émis par une source non autorisée')
        except Exception as e:
            raise ValidationError('Le token est invalide ou a expiré')


def register_social_user(provider, email, first_name, last_name):
    old_user = User.objects.filter(email=email)
    if old_user.exists():
        if provider == old_user[0].auth_provider:
            register_user = authenticate(email=email, password=settings.SOCIAL_AUTH_PASSWORD)
            
            if not register_user:
                raise AuthenticationFailed('Échec de l\'authentification, veuillez réessayer')
            
            # Uniformisation du format de retour pour utilisateur existant
            tokens = register_user.tokens()
            return {
                'email': register_user.email,
                'full_name': register_user.full_name,
                'access_token': str(tokens.get('access')),
                'refresh_token': str(tokens.get('refresh'))
            }
        else:
            raise AuthenticationFailed(
                f"Veuillez continuer votre connexion avec {old_user[0].auth_provider}"
            )
    else:
        if not first_name:
            first_name = email.split('@')[0]
        if not last_name:
            last_name = "_"

        new_user = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'password': settings.SOCIAL_AUTH_PASSWORD
        }
        
        # Utilisation d'une transaction atomique pour la création d'utilisateur et de profil
        with transaction.atomic():
            user = User.objects.create_user(**new_user)
            user.auth_provider = provider
            user.is_verified = True
            user.save()
            
            UserProfile.objects.create(
                user=user,
                has_onboarded=False
            )
        
        login_user = authenticate(email=email, password=settings.SOCIAL_AUTH_PASSWORD)
        
        if not login_user:
            raise AuthenticationFailed('Échec de la création du compte, veuillez réessayer')
       
        tokens = login_user.tokens()
        # Format déjà correct pour nouvel utilisateur
        return {
            'email': login_user.email,
            'full_name': login_user.full_name,
            'access_token': str(tokens.get('access')),
            'refresh_token': str(tokens.get('refresh'))
        }