from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Notification

User = get_user_model()


def create_notification(recipient, notification_type, message, related_object=None):
    """
    Crée une notification pour un utilisateur spécifique.
    
    Args:
        recipient (User): L'utilisateur qui recevra la notification
        notification_type (str): Le type de notification (doit correspondre aux choix dans le modèle)
        message (str): Le contenu de la notification
        related_object (Model instance, optional): L'objet associé à la notification (ex: Project, Application)
    
    Returns:
        Notification: L'instance de notification créée
        
    Raises:
        ValidationError: Si les données fournies ne sont pas valides
        ValueError: Si le type de notification n'est pas valide
    """
    # Validation des paramètres d'entrée
    if not recipient or not isinstance(recipient, User):
        raise ValidationError("Un utilisateur destinataire valide est requis")
    
    if not notification_type or not isinstance(notification_type, str):
        raise ValidationError("Un type de notification valide est requis")
    
    if not message or not isinstance(message, str):
        raise ValidationError("Un message de notification est requis")
    
    # Vérifier que le type de notification est valide
    valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPES]
    if notification_type not in valid_types:
        raise ValueError(f"Type de notification invalide: {notification_type}. Types valides: {valid_types}")
    
    content_type = None
    object_id = None
    
    if related_object:
        try:
            content_type = ContentType.objects.get_for_model(related_object)
            object_id = str(related_object.id)
        except Exception as e:
            raise ValidationError(f"Erreur lors de la récupération du type de contenu pour l'objet associé: {str(e)}")
    
    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                message=message,
                content_type=content_type,
                object_id=object_id
            )
            return notification
    except Exception as e:
        raise ValidationError(f"Erreur lors de la création de la notification: {str(e)}")


def mark_notifications_as_read(user, notification_ids=None):
    """
    Marque les notifications spécifiées comme lues.
    Si aucun ID n'est fourni, toutes les notifications de l'utilisateur sont marquées comme lues.
    
    Args:
        user (User): L'utilisateur propriétaire des notifications
        notification_ids (list, optional): Liste des IDs de notifications à marquer comme lues
    
    Returns:
        int: Le nombre de notifications marquées comme lues
        
    Raises:
        ValidationError: Si l'utilisateur n'est pas valide ou si les IDs sont invalides
    """
    # Validation des paramètres d'entrée
    if not user or not isinstance(user, User):
        raise ValidationError("Un utilisateur valide est requis")
    
    if notification_ids is not None and not isinstance(notification_ids, list):
        raise ValidationError("notification_ids doit être une liste")
    
    try:
        with transaction.atomic():
            notifications = Notification.objects.filter(recipient=user, is_read=False)
            
            if notification_ids:
                # Vérifier que tous les IDs appartiennent bien à l'utilisateur
                valid_ids = notifications.filter(id__in=notification_ids).values_list('id', flat=True)
                invalid_ids = set(notification_ids) - set(valid_ids)
                
                if invalid_ids:
                    raise ValidationError(f"IDs de notifications invalides ou non autorisés: {list(invalid_ids)}")
                
                notifications = notifications.filter(id__in=notification_ids)
            
            count = notifications.count()
            if count > 0:
                notifications.update(is_read=True)
            
            return count
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Erreur lors de la mise à jour des notifications: {str(e)}")


def get_notification_counts(user):
    """
    Récupère le nombre total de notifications et le nombre de notifications non lues pour un utilisateur.
    
    Args:
        user (User): L'utilisateur dont on veut compter les notifications
    
    Returns:
        dict: Dictionnaire contenant le nombre total et le nombre de notifications non lues
        
    Raises:
        ValidationError: Si l'utilisateur n'est pas valide
    """
    # Validation des paramètres d'entrée
    if not user or not isinstance(user, User):
        raise ValidationError("Un utilisateur valide est requis")
    
    try:
        total = Notification.objects.filter(recipient=user).count()
        unread = Notification.objects.filter(recipient=user, is_read=False).count()
        
        return {
            'total': total,
            'unread': unread
        }
    except Exception as e:
        raise ValidationError(f"Erreur lors de la récupération des compteurs de notifications: {str(e)}")


def delete_notification(user, notification_id):
    """
    Supprime une notification spécifique pour un utilisateur.
    
    Args:
        user (User): L'utilisateur propriétaire de la notification
        notification_id: L'ID de la notification à supprimer
    
    Returns:
        bool: True si la notification a été supprimée, False sinon
        
    Raises:
        ValidationError: Si l'utilisateur ou l'ID n'est pas valide
    """
    # Validation des paramètres d'entrée
    if not user or not isinstance(user, User):
        raise ValidationError("Un utilisateur valide est requis")
    
    if not notification_id:
        raise ValidationError("Un ID de notification est requis")
    
    try:
        with transaction.atomic():
            notification = Notification.objects.filter(
                id=notification_id, 
                recipient=user
            ).first()
            
            if not notification:
                return False
            
            notification.delete()
            return True
    except Exception as e:
        raise ValidationError(f"Erreur lors de la suppression de la notification: {str(e)}")


def bulk_delete_notifications(user, notification_ids):
    """
    Supprime plusieurs notifications pour un utilisateur.
    
    Args:
        user (User): L'utilisateur propriétaire des notifications
        notification_ids (list): Liste des IDs de notifications à supprimer
    
    Returns:
        int: Le nombre de notifications supprimées
        
    Raises:
        ValidationError: Si l'utilisateur ou les IDs ne sont pas valides
    """
    # Validation des paramètres d'entrée
    if not user or not isinstance(user, User):
        raise ValidationError("Un utilisateur valide est requis")
    
    if not notification_ids or not isinstance(notification_ids, list):
        raise ValidationError("Une liste d'IDs de notifications est requise")
    
    try:
        with transaction.atomic():
            notifications = Notification.objects.filter(
                id__in=notification_ids,
                recipient=user
            )
            
            count = notifications.count()
            if count > 0:
                notifications.delete()
            
            return count
    except Exception as e:
        raise ValidationError(f"Erreur lors de la suppression en lot des notifications: {str(e)}") 