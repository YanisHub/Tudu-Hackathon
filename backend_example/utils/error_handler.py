import functools
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework.exceptions import APIException, NotFound

def api_error_handler(f):
    """
    Décorateur pour standardiser la gestion des erreurs dans les vues API.
    Captures les exceptions communes et renvoie des réponses appropriées.
    Utilise la fonction api_response pour formater les réponses.
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        from utils.responses import api_response
        
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            response_data, status_code = api_response(
                success=False,
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except NotFound as e:
            response_data, status_code = api_response(
                success=False,
                message=str(e) if str(e) else "Ressource non trouvée",
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except PermissionDenied as e:
            response_data, status_code = api_response(
                success=False,
                message=str(e) if str(e) else "Permission refusée",
                status_code=status.HTTP_403_FORBIDDEN
            )
            return Response(response_data, status=status_code)
        except IntegrityError as e:
            # Transaction est annulée automatiquement en cas d'IntegrityError
            response_data, status_code = api_response(
                success=False,
                message="Erreur d'intégrité de la base de données",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except APIException as e:
            response_data, status_code = api_response(
                success=False,
                message=str(e),
                status_code=e.status_code
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            # Journaliser l'exception non prévue
            print(f"Erreur inattendue dans {f.__name__}: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message="Une erreur inattendue s'est produite",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)
    
    return wrapper 