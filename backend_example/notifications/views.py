from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import permissions

from .models import Notification
from .serializers import NotificationSerializer, NotificationCountSerializer
from .services import mark_notifications_as_read, get_notification_counts, bulk_delete_notifications
from utils.responses import api_response
from utils.error_handler import api_error_handler


class NotificationListView(ListAPIView):
    """
    API endpoint pour lister toutes les notifications de l'utilisateur connecté.
    Permet de filtrer par is_read et notification_type.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(recipient=user)
        
        # Filtrer par statut de lecture
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
        
        # Filtrer par type de notification
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset.order_by('-created_at')
    
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


class NotificationDetailView(APIView):
    """
    API endpoint pour récupérer, mettre à jour ou supprimer une notification spécifique.
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        """Récupère la notification et vérifie la propriété"""
        return get_object_or_404(Notification, id=pk, recipient=user)
    
    @api_error_handler
    def get(self, request, pk):
        """Récupère une notification spécifique"""
        notification = self.get_object(pk, request.user)
        serializer = NotificationSerializer(notification)
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def patch(self, request, pk):
        """Met à jour partiellement une notification (seul is_read peut être modifié)"""
        notification = self.get_object(pk, request.user)
        
        # Validation des données d'entrée
        if 'is_read' not in request.data:
            response_data, status_code = api_response(
                success=False,
                message='Le champ is_read est requis pour cette opération',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        is_read = request.data.get('is_read')
        if not isinstance(is_read, bool):
            response_data, status_code = api_response(
                success=False,
                message='Le champ is_read doit être un booléen (true ou false)',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Utilisation d'une transaction atomique
        with transaction.atomic():
            notification.is_read = is_read
            notification.save(update_fields=['is_read'])
        
        serializer = NotificationSerializer(notification)
        response_data, status_code = api_response(
            success=True,
            message='Notification mise à jour avec succès',
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def delete(self, request, pk):
        """Supprime une notification"""
        notification = self.get_object(pk, request.user)
        
        with transaction.atomic():
            notification.delete()
            
        response_data, status_code = api_response(
            success=True,
            message='Notification supprimée avec succès',
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)


class MarkNotificationsReadView(APIView):
    """
    API endpoint pour marquer les notifications spécifiées comme lues.
    Si aucun ID n'est fourni, toutes les notifications de l'utilisateur sont marquées comme lues.
    """
    permission_classes = [IsAuthenticated]
    
    @api_error_handler
    def post(self, request):
        """Marque les notifications comme lues"""
        notification_ids = request.data.get('notification_ids', [])
        
        # Validation : si notification_ids est fourni mais vide, retourner une erreur
        if 'notification_ids' in request.data and not notification_ids:
            response_data, status_code = api_response(
                success=False,
                message='Aucune notification spécifiée. Veuillez fournir une liste d\'IDs ou omettre ce champ pour marquer toutes les notifications comme lues.',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Validation du format des IDs si fournis
        if notification_ids and not isinstance(notification_ids, list):
            response_data, status_code = api_response(
                success=False,
                message='notification_ids doit être une liste d\'identifiants',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        try:
            with transaction.atomic():
                count = mark_notifications_as_read(request.user, notification_ids)
                
                if count == 0:
                    message = 'Aucune notification à marquer comme lue'
                elif count == 1:
                    message = '1 notification marquée comme lue'
                else:
                    message = f'{count} notifications marquées comme lues'
                
                response_data, status_code = api_response(
                    success=True,
                    message=message,
                    data={'notifications_updated': count},
                    status_code=status.HTTP_200_OK
                )
                return Response(response_data, status=status_code)
                
        except Exception as e:
            # Journaliser l'erreur pour les administrateurs
            print(f"Unexpected error in MarkNotificationsReadView: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='Une erreur inattendue est survenue lors de la mise à jour des notifications',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)


class NotificationCountView(APIView):
    """
    API endpoint pour retourner le nombre total de notifications et le nombre de notifications non lues.
    """
    permission_classes = [IsAuthenticated]
    
    @api_error_handler
    def get(self, request):
        """Récupère les compteurs de notifications pour l'utilisateur connecté"""
        try:
            counts = get_notification_counts(request.user)
            serializer = NotificationCountSerializer(data=counts)
            
            if not serializer.is_valid():
                response_data, status_code = api_response(
                    success=False,
                    message='Erreur lors de la sérialisation des données de comptage',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                return Response(response_data, status=status_code)
            
            response_data, status_code = api_response(
                success=True,
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        except Exception as e:
            # Journaliser l'erreur pour les administrateurs
            print(f"Unexpected error in NotificationCountView: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='Une erreur inattendue est survenue lors de la récupération des compteurs',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)


class BulkDeleteNotificationsView(APIView):
    """
    API endpoint pour supprimer plusieurs notifications en une seule fois.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @api_error_handler
    def delete(self, request):
        """Supprime plusieurs notifications en lot"""
        notification_ids = request.data.get('notification_ids', [])
        
        # Validation des données d'entrée
        if not notification_ids:
            response_data, status_code = api_response(
                success=False,
                message='Une liste d\'IDs de notifications est requise',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        if not isinstance(notification_ids, list):
            response_data, status_code = api_response(
                success=False,
                message='notification_ids doit être une liste d\'identifiants',
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        try:
            count = bulk_delete_notifications(request.user, notification_ids)
            
            if count == 0:
                message = 'Aucune notification trouvée à supprimer'
            elif count == 1:
                message = '1 notification supprimée avec succès'
            else:
                message = f'{count} notifications supprimées avec succès'
            
            response_data, status_code = api_response(
                success=True,
                message=message,
                data={'notifications_deleted': count},
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        except ValidationError as e:
            response_data, status_code = api_response(
                success=False,
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            # Journaliser l'erreur pour les administrateurs
            print(f"Unexpected error in BulkDeleteNotificationsView: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='Une erreur inattendue est survenue lors de la suppression des notifications',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)
