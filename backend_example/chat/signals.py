from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.models import Application
from .models import ChatSession, ChatMessage


@receiver(post_save, sender=Application)
def create_chat_for_accepted_application(sender, instance, created, **kwargs):
    """
    Crée automatiquement une session de chat lorsqu'une candidature est acceptée.
    """
    # Vérifier si l'application a été mise à jour (pas juste créée) et que le statut est "accepted"
    if instance.status == 'accepted':
        # Vérifier si une session de chat existe déjà pour ce projet
        project = instance.project
        
        # S'assurer que le collaborateur est bien assigné au projet
        if not project.collaborator:
            project.collaborator = instance.applicant
            project.status = 'in_progress'
            project.save()
        
        # Créer une session de chat si elle n'existe pas
        chat_session, chat_created = ChatSession.objects.get_or_create(project=project)
        
        # Si une nouvelle session de chat est créée, ajouter un message automatique
        if chat_created:
            ChatMessage.objects.create(
                chat_session=chat_session,
                sender=project.owner,
                content=f"Bienvenue ! La candidature pour le projet '{project.title}' a été acceptée. Vous pouvez maintenant discuter des détails du projet ici."
            ) 