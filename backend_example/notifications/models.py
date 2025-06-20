import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Notification(models.Model):
    """
    Modèle représentant une notification envoyée à un utilisateur concernant un événement spécifique.
    
    Ce modèle permet de créer des notifications liées à n'importe quel objet du système
    grâce à la relation générique (GenericForeignKey).
    """
    NOTIFICATION_TYPES = (
        ('project_created', _('Projet créé')),
        ('application_received', _('Nouvelle candidature reçue')),
        ('application_accepted', _('Candidature acceptée')),
        ('application_rejected', _('Candidature rejetée')),
        ('project_assigned', _('Projet assigné')),
        ('project_status_update', _('Statut du projet mis à jour')),
        ('project_completed', _('Projet terminé')),
        ('project_revision_requested', _('Révision du projet demandée')),
        ('new_message', _('Nouveau message de chat')),
        ('payment_held', _('Paiement bloqué en dépôt de garantie')),
        ('payment_released', _('Paiement libéré')),
        ('payment_failed', _('Échec du paiement')),
    )

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text=_("Identifiant unique de la notification")
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text=_("Utilisateur destinataire de la notification")
    )
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES,
        help_text=_("Type de notification")
    )
    message = models.TextField(
        blank=True, 
        help_text=_("Contenu du message de notification")
    )
    is_read = models.BooleanField(
        default=False,
        help_text=_("Indique si la notification a été lue")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Date et heure de création de la notification")
    )
    read_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("Date et heure de lecture de la notification")
    )

    # Relation générique pour lier à l'objet qui a déclenché la notification
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text=_("Type de contenu de l'objet associé")
    )
    object_id = models.CharField(
        max_length=36, 
        null=True, 
        blank=True,
        help_text=_("Identifiant de l'objet associé")
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Notification pour {self.recipient.email} - Type: {self.get_notification_type_display()}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
            models.Index(fields=["notification_type"]),
        ]
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")

    def save(self, *args, **kwargs):
        """
        Override de la méthode save pour gérer automatiquement read_at.
        """
        # Si la notification passe de non lue à lue, enregistrer la date de lecture
        if self.pk and self.is_read and not self.read_at:
            try:
                old_instance = Notification.objects.get(pk=self.pk)
                if not old_instance.is_read:
                    self.read_at = timezone.now()
            except Notification.DoesNotExist:
                pass
        
        # Si on marque comme non lue, effacer la date de lecture
        elif not self.is_read and self.read_at:
            self.read_at = None
            
        super().save(*args, **kwargs)

    def mark_as_read(self):
        """
        Marque la notification comme lue et enregistre la date de lecture.
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """
        Marque la notification comme non lue et efface la date de lecture.
        """
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def is_recent(self):
        """
        Retourne True si la notification a été créée dans les dernières 24 heures.
        """
        if not self.created_at:
            return False
        return timezone.now() - self.created_at <= timezone.timedelta(hours=24)

    @property
    def age_in_days(self):
        """
        Retourne l'âge de la notification en jours.
        """
        if not self.created_at:
            return 0
        return (timezone.now() - self.created_at).days

    def get_related_object_info(self):
        """
        Retourne des informations sur l'objet associé à la notification.
        """
        if self.content_object:
            return {
                'type': self.content_type.model,
                'app': self.content_type.app_label,
                'id': self.object_id,
                'object': self.content_object
            }
        return None

    @classmethod
    def get_unread_count_for_user(cls, user):
        """
        Retourne le nombre de notifications non lues pour un utilisateur.
        """
        return cls.objects.filter(recipient=user, is_read=False).count()

    @classmethod
    def mark_all_as_read_for_user(cls, user):
        """
        Marque toutes les notifications d'un utilisateur comme lues.
        """
        return cls.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
