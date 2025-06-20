from rest_framework import serializers
from .helpers import Google, register_social_user
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from django.utils.translation import gettext_lazy as _


class GoogleSignInSerializer(serializers.Serializer):
    access_token = serializers.CharField(
        min_length=6, 
        error_messages={
            'required': _('Le token d\'accès est requis'),
            'min_length': _('Le token d\'accès doit comporter au moins 6 caractères'),
            'blank': _('Le token d\'accès ne peut pas être vide')
        }
    )

    def validate_access_token(self, access_token):
        google_user_data = Google.validate(access_token)
        
        try:
            userid = google_user_data['sub']
        except (KeyError, TypeError):
            raise ValidationError('Token invalide: identifiant utilisateur manquant')

        if google_user_data.get('aud') != settings.GOOGLE_CLIENT_ID:
            raise AuthenticationFailed('Impossible de vérifier l\'utilisateur: client non autorisé')
            
        email = google_user_data.get('email')
        if not email:
            raise ValidationError('L\'email est requis pour l\'authentification')
            
        first_name = google_user_data.get('given_name', '')
        last_name = google_user_data.get('family_name', '')
        provider = 'google'

        return register_social_user(provider, email, first_name, last_name)

        