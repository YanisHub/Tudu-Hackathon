from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from .models import Notification

User = get_user_model()


class ContentTypeSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle ContentType.
    """
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Notification.
    Fournit une représentation complète d'une notification avec des informations formatées.
    """
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    content_type_info = ContentTypeSerializer(source='content_type', read_only=True)
    created_at_formatted = serializers.SerializerMethodField()
    read_at_formatted = serializers.SerializerMethodField()
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    is_recent = serializers.BooleanField(read_only=True)
    age_in_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'notification_type_display', 
            'message', 'is_read', 'created_at', 'created_at_formatted',
            'read_at', 'read_at_formatted', 'content_type', 'content_type_info', 
            'object_id', 'recipient_email', 'is_recent', 'age_in_days'
        ]
        read_only_fields = [
            'recipient', 'notification_type', 'message', 
            'content_type', 'object_id', 'created_at', 'read_at'
        ]
    
    def get_created_at_formatted(self, obj):
        """
        Retourne la date de création formatée en français.
        """
        if not obj.created_at:
            return None
        return obj.created_at.strftime("%d %b %Y, %H:%M")
    
    def get_read_at_formatted(self, obj):
        """
        Retourne la date de lecture formatée en français.
        """
        if not obj.read_at:
            return None
        return obj.read_at.strftime("%d %b %Y, %H:%M")
    
    def validate_is_read(self, value):
        """
        Valide le champ is_read.
        """
        if not isinstance(value, bool):
            raise serializers.ValidationError(
                "Le champ is_read doit être un booléen (true ou false)"
            )
        return value


class NotificationCountSerializer(serializers.Serializer):
    """
    Serializer pour retourner les compteurs de notifications.
    """
    total = serializers.IntegerField(min_value=0, help_text="Nombre total de notifications")
    unread = serializers.IntegerField(min_value=0, help_text="Nombre de notifications non lues")
    
    def validate(self, data):
        """
        Validation globale des données de comptage.
        """
        total = data.get('total', 0)
        unread = data.get('unread', 0)
        
        if unread > total:
            raise serializers.ValidationError(
                "Le nombre de notifications non lues ne peut pas être supérieur au nombre total"
            )
        
        return data


class BulkActionSerializer(serializers.Serializer):
    """
    Serializer pour les actions en lot sur les notifications.
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="Liste des IDs de notifications à traiter"
    )
    
    def validate_notification_ids(self, value):
        """
        Valide la liste des IDs de notifications.
        """
        if not value:
            raise serializers.ValidationError(
                "Au moins un ID de notification est requis"
            )
        
        # Vérifier la longueur raisonnable de la liste
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Trop de notifications sélectionnées. Maximum: 1000"
            )
        
        # Supprimer les doublons
        unique_ids = list(set(value))
        if len(unique_ids) != len(value):
            raise serializers.ValidationError(
                "Des IDs de notifications sont dupliqués dans la liste"
            )
        
        return unique_ids


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de notifications (usage interne/admin).
    """
    class Meta:
        model = Notification
        fields = [
            'recipient', 'notification_type', 'message',
            'content_type', 'object_id'
        ]
    
    def validate_notification_type(self, value):
        """
        Valide le type de notification.
        """
        valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Type de notification invalide. Types valides: {valid_types}"
            )
        return value
    
    def validate_message(self, value):
        """
        Valide le message de la notification.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Le message de notification ne peut pas être vide"
            )
        
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Le message de notification ne peut pas dépasser 1000 caractères"
            )
        
        return value.strip()
    
    def validate(self, data):
        """
        Validation globale des données de création.
        """
        recipient = data.get('recipient')
        if recipient and not recipient.is_active:
            raise serializers.ValidationError(
                "Impossible d'envoyer une notification à un utilisateur inactif"
            )
        
        return data 