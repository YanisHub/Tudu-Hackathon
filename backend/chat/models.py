import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from projects.models import Project


class ChatSession(models.Model):
    """
    Represents a chat session between the project owner and the collaborator 
    once a project is in progress.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='chat_session')
    # Participants can be inferred from project.owner and project.collaborator
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Timestamp of the last message

    def __str__(self):
        return f"Chat for Project: {self.project.title}"

    class Meta:
        ordering = ['-updated_at']


class ChatMessage(models.Model):
    """
    Represents a single message within a ChatSession.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)

    def __str__(self):
        return f"Message from {self.sender.email} at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']
