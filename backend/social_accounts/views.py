from rest_framework import status
from rest_framework.response import Response
from .serializers import GoogleSignInSerializer
from rest_framework.generics import GenericAPIView

from utils.responses import api_response
from utils.error_handler import api_error_handler


class GoogleOauthSignInview(GenericAPIView):
    """
    API endpoint pour l'authentification avec Google OAuth2.
    """
    serializer_class = GoogleSignInSerializer

    @api_error_handler
    def post(self, request):
        # Vérifier que les données requises sont présentes
        if not request.data.get('access_token'):
            response_data, status_code = api_response(
                success=False,
                message='Le token d\'accès Google est requis',
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
        
        data = serializer.validated_data['access_token']
        response_data, status_code = api_response(
            success=True,
            message='Authentification Google réussie',
            data=data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code) 