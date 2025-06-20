from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.models import Application
from projects.models import Project
from chat.models import ChatMessage

from .services import create_notification


@receiver(post_save, sender=Application)
def application_status_changed(sender, instance, created, **kwargs):
    """
    Génère des notifications lorsqu'une candidature est créée ou que son statut change.
    """
    if created:
        # Nouvelle candidature créée - notifier le propriétaire du projet
        project_owner = instance.project.owner
        create_notification(
            recipient=project_owner,
            notification_type='application_received',
            message=f"Nouvelle candidature pour votre projet '{instance.project.title}'",
            related_object=instance
        )
    else:
        # Candidature mise à jour
        if instance.status == 'accepted':
            # Notifier le candidat que sa candidature a été acceptée
            create_notification(
                recipient=instance.applicant,
                notification_type='application_accepted',
                message=f"Votre candidature pour le projet '{instance.project.title}' a été acceptée",
                related_object=instance
            )
            
            # Notifier le candidat qu'il est maintenant collaborateur du projet
            create_notification(
                recipient=instance.applicant,
                notification_type='project_assigned',
                message=f"Vous êtes maintenant collaborateur du projet '{instance.project.title}'",
                related_object=instance.project
            )
            
        elif instance.status == 'rejected':
            # Notifier le candidat que sa candidature a été rejetée
            create_notification(
                recipient=instance.applicant,
                notification_type='application_rejected',
                message=f"Votre candidature pour le projet '{instance.project.title}' a été rejetée",
                related_object=instance
            )


@receiver(post_save, sender=Project)
def project_status_changed(sender, instance, created, **kwargs):
    """
    Génère des notifications lorsqu'un projet est créé ou que son statut change.
    """
    if created:
        return  # Ne rien faire pour les nouveaux projets
    
    # Vérifier si le collaborateur est assigné
    if instance.collaborator:
        # Notifier le collaborateur si le statut du projet a changé
        if instance.status == 'completed':
            create_notification(
                recipient=instance.collaborator,
                notification_type='project_completed',
                message=f"Le projet '{instance.title}' a été marqué comme terminé",
                related_object=instance
            )
            # Notifier aussi le propriétaire
            create_notification(
                recipient=instance.owner,
                notification_type='project_completed',
                message=f"Votre projet '{instance.title}' a été marqué comme terminé",
                related_object=instance
            )
        
        elif instance.status == 'in_review':
            create_notification(
                recipient=instance.owner,
                notification_type='project_status_update',
                message=f"Le projet '{instance.title}' est en cours de révision",
                related_object=instance
            )


@receiver(post_save, sender=ChatMessage)
def new_chat_message(sender, instance, created, **kwargs):
    """
    Génère une notification lorsqu'un nouveau message est envoyé.
    """
    if not created:
        return  # Ne traiter que les nouveaux messages
    
    project = instance.chat_session.project
    
    # Déterminer le destinataire (celui qui n'a pas envoyé le message)
    if instance.sender == project.owner:
        recipient = project.collaborator
    else:
        recipient = project.owner
    
    # S'assurer que le destinataire existe
    if recipient:
        create_notification(
            recipient=recipient,
            notification_type='new_message',
            message=f"Nouveau message de {instance.sender.full_name or instance.sender.email} dans le projet '{project.title}'",
            related_object=instance
        ) 