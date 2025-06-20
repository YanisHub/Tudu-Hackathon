import uuid
from django.db import models
from django.conf import settings

from accounts.models import ExpertiseArea



class Project(models.Model):
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('open', 'Open for applications'),
        ('in_progress', 'In Progress'),
        ('in_review', 'In Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    collaborator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null = True, blank=True, related_name='assigned_projects')
    title = models.CharField(max_length=255)
    description = models.TextField()
    expertise_required = models.ManyToManyField(ExpertiseArea, related_name='required_in_projects', blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    
    estimated_hours = models.PositiveIntegerField(null = True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    
    deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null = True, blank = True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    
class ProjectAttachment(models.Model):    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='project_attachments/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="Size in octets")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_attachments')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.project.title}"
    
    class Meta:
        ordering = ['-created_at']