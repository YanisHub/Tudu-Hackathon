# Standard library imports
import hashlib

# Django imports
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db import transaction

# Rest framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import filters, permissions, status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework_simplejwt.tokens import TokenError

# Local imports
from .serializers import (
    ExpertiseAreaSerializer,
    LoginSerializer,
    LogoutUserSerializer,
    PasswordResetRequestSerializer,
    SetNewPasswordSerializer,
    UserExpertiseSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
    UserSerializer
)
from utils.responses import api_response
from utils.error_handler import api_error_handler

from .permissions import IsOwnerOrReadOnly
from .utils import send_generated_otp_to_email
from .models import User, UserProfile, ExpertiseArea, UserExpertise, OneTimePassword



class RegisterView(GenericAPIView):
    serializer_class = UserRegisterSerializer

    @api_error_handler
    def post(self, request):
        user = request.data
        serializer=self.serializer_class(data=user)
        
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Utilisation d'une transaction atomique pour la création d'utilisateur et de profil
        with transaction.atomic():
            serializer.save()
            user_data=serializer.data
            send_generated_otp_to_email(user_data['email'], request)
            response_data, status_code = api_response(
                success=True,
                message='Merci pour votre inscription. Un code de vérification a été envoyé à votre adresse email',
                data=user_data,
                status_code=status.HTTP_201_CREATED
            )
            return Response(response_data, status=status_code)




class VerifyUserEmail(APIView):
    
    def post(self, request):
        try:
            passcode = request.data.get('otp')
            if not passcode:
                response_data, status_code = api_response(
                    success=False,
                    message='Le code de vérification est requis',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)
                
            passcode_str = str(passcode)
            
            # Récupérer tous les OTP non expirés (moins de 15 minutes)
            valid_otps = OneTimePassword.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
            )
            user = None
            for otp_obj in valid_otps:
                # Extraire le sel et le hash
                stored_salt_hex = otp_obj.otp_hash[:64]
                stored_hash = otp_obj.otp_hash[64:]
                
                # Recréer le sel
                salt = bytes.fromhex(stored_salt_hex)
                
                # Recalculer le hash avec le code entré
                hashed_input = hashlib.pbkdf2_hmac(
                    'sha256',
                    passcode_str.encode('utf-8'),
                    salt,
                    10000
                )
                
                # Comparer les hash
                if stored_hash == hashlib.sha256(hashed_input).hexdigest():
                    user = otp_obj.user
                    break
            
            if user and not user.is_verified:
                user.is_verified = True
                user.save()
                # Supprimer l'OTP après usage
                OneTimePassword.objects.filter(user=user).delete()
                response_data, status_code = api_response(
                    success=True,
                    message='Email vérifié avec succès',
                    status_code=status.HTTP_200_OK
                )
                return Response(response_data, status=status_code)
                
            response_data, status_code = api_response(
                success=False,
                message='Code de vérification invalide ou expiré',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        except ValueError as e:
            # Erreur de conversion de données
            response_data, status_code = api_response(
                success=False,
                message='Format de données invalide',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except (TypeError, AttributeError) as e:
            # Erreur de manipulation d'objets
            response_data, status_code = api_response(
                success=False,
                message='Erreur de traitement des données',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            # Journaliser l'erreur pour les administrateurs
            print(f"Unexpected error in VerifyUserEmail: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='Une erreur inattendue est survenue, veuillez réessayer plus tard',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)


class LoginUserView(GenericAPIView):
    serializer_class=LoginSerializer
    
    @api_error_handler
    def post(self, request):
        # Vérifier que les données requises sont présentes
        if not request.data.get('email') or not request.data.get('password'):
            response_data, status_code = api_response(
                success=False,
                message='Email et mot de passe sont requis',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        response_data, status_code = api_response(
            success=True,
            message='Connexion réussie',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class PasswordResetRequestView(GenericAPIView):
    serializer_class=PasswordResetRequestSerializer

    def post(self, request):
        serializer=self.serializer_class(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        response_data, status_code = api_response(
            success=True,
            message='Nous vous avons envoyé un lien pour réinitialiser votre mot de passe',
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    
class PasswordResetConfirm(GenericAPIView):

    def get(self, request, uidb64, token):
        try:
            user_id=smart_str(urlsafe_base64_decode(uidb64))
            user=User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                response_data, status_code = api_response(
                    success=False,
                    message='Le token est invalide ou a expiré',
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
                return Response(response_data, status=status_code)
                
            response_data, status_code = api_response(
                success=True, 
                message='Les identifiants sont valides', 
                data={
                    'uidb64': uidb64, 
                    'token': token
                },
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)

        except DjangoUnicodeDecodeError as identifier:
            response_data, status_code = api_response(
                success=False,
                message='Le token est invalide ou a expiré',
                status_code=status.HTTP_401_UNAUTHORIZED
            )
            return Response(response_data, status=status_code)

class SetNewPasswordView(GenericAPIView):
    serializer_class=SetNewPasswordSerializer

    def patch(self, request):
        try:
            # Vérifier que les données requises sont présentes
            required_fields = ['password', 'confirm_password', 'uidb64', 'token']
            for field in required_fields:
                if field not in request.data:
                    response_data, status_code = api_response(
                        success=False,
                        message=f'Le champ {field} est requis',
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                    return Response(response_data, status=status_code)
            
            serializer=self.serializer_class(data=request.data)
            if serializer.is_valid():
                # La validation du token est déjà gérée dans le serializer
                user_id=force_str(urlsafe_base64_decode(serializer.validated_data.get('uidb64')))
                user=User.objects.get(id=user_id)
                user.set_password(serializer.validated_data.get('password'))
                user.save()
                
                response_data, status_code = api_response(
                    success=True,
                    message='Réinitialisation du mot de passe réussie',
                    status_code=status.HTTP_200_OK
                )
                return Response(response_data, status=status_code)
            else:
                response_data, status_code = api_response(
                    success=False,
                    message=serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)
        except DjangoUnicodeDecodeError:
            response_data, status_code = api_response(
                success=False,
                message='Format uidb64 invalide',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except User.DoesNotExist:
            response_data, status_code = api_response(
                success=False,
                message='Utilisateur non trouvé',
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            # Journaliser l'erreur pour les administrateurs
            print(f"Unexpected error in SetNewPasswordView: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='Une erreur inattendue est survenue lors de la réinitialisation du mot de passe',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)


class TestingAuthenticatedReq(GenericAPIView):
    permission_classes=[permissions.IsAuthenticated]

    def get(self, request):
        response_data, status_code = api_response(
            success=True,
            message='L\'authentification fonctionne correctement',
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)

class LogoutApiView(GenericAPIView):
    serializer_class=LogoutUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @api_error_handler
    def post(self, request):
        # Vérifier que le token de rafraîchissement est présent
        if not request.data.get('refresh_token'):
            response_data, status_code = api_response(
                success=False,
                message='Le token de rafraîchissement est requis',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        try:
            # Essayer de mettre le token en liste noire
            serializer.save()
            response_data, status_code = api_response(
                success=True,
                message='Déconnexion réussie',
                status_code=status.HTTP_204_NO_CONTENT
            )
            return Response(response_data, status=status_code)
        except TokenError:
            # Capture spécifique des erreurs de token
            response_data, status_code = api_response(
                success=False,
                message='Token invalide ou expiré',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)

    
class UserProfileView(APIView):
    """
    API endpoint for managing the authenticated user's profile.
    GET: Retrieve the user's profile
    PUT/PATCH: Update the user's profile
    DELETE: Delete the user's profile
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    @api_error_handler
    def get(self, request):
        """Get the profile of the currently authenticated user"""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def put(self, request):
        """Update the profile of the currently authenticated user"""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message='Profil mis à jour avec succès',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def patch(self, request):
        """Partially update the profile of the currently authenticated user"""
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message='Profil mis à jour avec succès',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def delete(self, request):
        """Delete the profile of the currently authenticated user"""
        profile = request.user.profile
        profile.delete()
        response_data, status_code = api_response(
            success=True,
            message='Profil supprimé avec succès',
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)


class ExpertiseAreaListView(ListAPIView):
    """
    API endpoint for listing expertise areas.
    """
    queryset = ExpertiseArea.objects.all()
    serializer_class = ExpertiseAreaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def list(self, request, *args, **kwargs):
        """Override the list method to standardize response format"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            response_data, status_code = api_response(
                success=True,
                data=paginated_response.data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        serializer = self.get_serializer(queryset, many=True)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class ExpertiseAreaCreateView(APIView):
    """
    API endpoint for creating expertise areas.
    """
    permission_classes = [permissions.IsAdminUser]
    
    @api_error_handler
    def post(self, request):
        """Create a new expertise area"""
        serializer = ExpertiseAreaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message='Domaine d\'expertise créé avec succès',
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
        return Response(response_data, status=status_code)


class ExpertiseAreaDetailView(APIView):
    """
    API endpoint for retrieving, updating, and deleting expertise areas.
    """
    def get_permissions(self):
        """
        Read operations available to all authenticated users,
        Write operations restricted to admin users
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_object(self, pk):
        """Get the expertise area by primary key"""
        return get_object_or_404(ExpertiseArea, pk=pk)
    
    @api_error_handler
    def get(self, request, pk):
        """Retrieve an expertise area"""
        expertise = self.get_object(pk)
        serializer = ExpertiseAreaSerializer(expertise)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def put(self, request, pk):
        """Update an expertise area"""
        expertise = self.get_object(pk)
        serializer = ExpertiseAreaSerializer(expertise, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message='Domaine d\'expertise mis à jour avec succès',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def patch(self, request, pk):
        """Partially update an expertise area"""
        expertise = self.get_object(pk)
        serializer = ExpertiseAreaSerializer(expertise, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message='Domaine d\'expertise mis à jour avec succès',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def delete(self, request, pk):
        """Delete an expertise area"""
        expertise = self.get_object(pk)
        expertise.delete()
        response_data, status_code = api_response(
            success=True,
            message='Domaine d\'expertise supprimé avec succès',
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)


class UserExpertiseListView(APIView):
    """
    API endpoint for listing and creating user expertise records.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    @api_error_handler
    def get(self, request):
        """Return only the user's own expertise records"""
        user_expertise = UserExpertise.objects.filter(user=request.user)
        serializer = UserExpertiseSerializer(user_expertise, many=True)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def post(self, request):
        """Create a new user expertise, handling duplicates"""
        # Vérification de duplication maintenue dans la vue
        expertise_id = request.data.get('expertise')
        if expertise_id and UserExpertise.objects.filter(
            user=request.user, 
            expertise_id=expertise_id
        ).exists():
            response_data, status_code = api_response(
                success=False,
                message="Cette expertise existe déjà dans votre profil.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Utilisation d'une transaction atomique pour garantir la cohérence des données
        with transaction.atomic():
            # Vérifier que l'expertise existe
            if expertise_id and not ExpertiseArea.objects.filter(id=expertise_id).exists():
                response_data, status_code = api_response(
                    success=False,
                    message="L'expertise spécifiée n'existe pas",
                    status_code=status.HTTP_404_NOT_FOUND
                )
                return Response(response_data, status=status_code)
                
            # Normal creation flow
            serializer = UserExpertiseSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            response_data, status_code = api_response(
                success=True,
                message="Expertise ajoutée avec succès à votre profil",
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
            return Response(response_data, status=status_code)


class UserExpertiseDetailView(APIView):
    """
    API endpoint for retrieving, updating, and deleting user expertise records.
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_object(self, pk):
        """Get the user expertise by primary key and verify ownership"""
        return get_object_or_404(UserExpertise, pk=pk, user=self.request.user)
    
    @api_error_handler
    def get(self, request, pk):
        """Retrieve a user expertise record"""
        expertise = self.get_object(pk)
        serializer = UserExpertiseSerializer(expertise)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def put(self, request, pk):
        """Update a user expertise, handling potential conflicts"""
        # La vérification de conflit reste dans la vue
        expertise_id = request.data.get('expertise')
        if expertise_id:
            instance = self.get_object(pk)
            if UserExpertise.objects.filter(
                Q(user=request.user) & 
                Q(expertise_id=expertise_id) & 
                ~Q(id=instance.id)
            ).exists():
                response_data, status_code = api_response(
                    success=False,
                    message="Cette expertise existe déjà dans un autre enregistrement de votre profil.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)
        
        # Normal update flow
        expertise = self.get_object(pk)
        serializer = UserExpertiseSerializer(expertise, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message="Expertise utilisateur mise à jour avec succès",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def patch(self, request, pk):
        """Partially update a user expertise"""
        expertise = self.get_object(pk)
        serializer = UserExpertiseSerializer(expertise, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message="Expertise utilisateur mise à jour avec succès",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def delete(self, request, pk):
        """Delete a user expertise record"""
        expertise = self.get_object(pk)
        expertise.delete()
        response_data, status_code = api_response(
            success=True,
            message="Expertise utilisateur supprimée avec succès",
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)


class AvailableExpertiseView(APIView):
    """
    API endpoint to get expertise areas that are not already in the user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return expertise areas that are not already in the user's profile"""
        # Get all expertise areas user already has
        user_expertise_ids = UserExpertise.objects.filter(
            user=request.user
        ).values_list('expertise_id', flat=True)
        
        # Get all expertise areas excluding those the user already has
        available_expertise = ExpertiseArea.objects.exclude(
            id__in=user_expertise_ids
        )
        
        # Filter by search query if provided
        search_query = request.query_params.get('search', None)
        if search_query:
            available_expertise = available_expertise.filter(name__icontains=search_query)
        
        serializer = ExpertiseAreaSerializer(available_expertise, many=True)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class CurrentUserView(APIView):
    """
    API endpoint to get data about the current authenticated user,
    including profile and expertise information.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return data for the current authenticated user"""
        user = request.user
        profile = request.user.profile
        expertise = UserExpertise.objects.filter(user=user)
        
        # Prepare response data
        user_data = {
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(profile).data,
            'expertise': UserExpertiseSerializer(expertise, many=True).data
        }
        
        response_data, status_code = api_response(
            success=True,
            data=user_data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
 