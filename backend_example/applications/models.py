import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from projects.models import Project


class Application(models.Model):
    """
    Represents a user's application to work on a project.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('rejected', _('Rejected')),
        ('withdrawn', _('Withdrawn')), # If the applicant withdraws
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True, help_text=_("Optional cover letter or message for the application."))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Tracks status changes (accepted, rejected, etc.)

    def __str__(self):
        return f"Application by {self.applicant.email} for {self.project.title}"

    class Meta:
        unique_together = ('project', 'applicant') # Ensure a user applies only once per project
        ordering = ['-applied_at']

