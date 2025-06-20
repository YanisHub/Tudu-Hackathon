from django.utils import timezone
from rest_framework import serializers

from .models import (
    Project,
    ProjectAttachment
)

from accounts.serializers import (
    UserSerializer,
    ExpertiseAreaSerializer
)

class ProjectAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_details = UserSerializer(source = 'uploaded_by', read_only = True)
    
    class Meta:
        model = ProjectAttachment
        fields = ['id', 'project', 'file', 'file_name', 'file_size', 'uploaded_by',
                  'uploaded_by_details', 'description', 'created_at']
        read_only_fields = ['id', 'project', 'uploaded_by', 'file_name', 'file_size', 'uploaded_by_details', 'created_at']

    def get_file_size(self, obj):
        return obj.file.size
    
    def get_file_name(self, obj):
        return obj.file.name
        
    def create(self, validated_data):
        project = validated_data.get('project')
        request = self.context['request']
        
        if request.user != project.owner:
            raise serializers.ValidationError("Vous n'avez pas les permissions pour ajouter des pièces jointes à ce projet")
    
        return super().create(validated_data)


class ProjectAttachmentSimpleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour ProjectAttachment qui n'expose que le champ 'file'.
    Les autres champs sont remplis automatiquement lors de la création.
    """
    class Meta:
        model = ProjectAttachment
        fields = ['id', 'file']
        read_only_fields = ['id']
        
    def create(self, validated_data):
        file = validated_data.get('file')
        project = self.context.get('project')
        request = self.context.get('request')
        
        if not project:
            raise serializers.ValidationError("Projet non spécifié")
            
        if not request or not request.user:
            raise serializers.ValidationError("Utilisateur non authentifié")
            
        # Auto-remplir les autres champs
        attachment = ProjectAttachment(
            project=project,
            file=file,
            file_name=file.name,
            file_size=file.size,
            uploaded_by=request.user
        )
        attachment.save()
        
        return attachment


class ProjectSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source = 'owner', read_only = True)
    collaborator_details = UserSerializer(source = 'collaborator', read_only = True)
    attachments = ProjectAttachmentSerializer(many = True, read_only = True)
    expertise_required_details = ExpertiseAreaSerializer(source='expertise_required', many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'owner', 'owner_details', 'collaborator', 'collaborator_details',
                  'title', 'description', 'status', 'expertise_required', 
                  'expertise_required_details', 'estimated_hours', 'budget', 'is_published',
                  'deadline', 'attachments','created_at', 'updated_at', 'completed_at']
        
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner', 'collaborator', 'status', 'completed_at']
        
    
    def create(self, validated_data):
        expertise_required = validated_data.pop('expertise_required', [])
        project = Project.objects.create(**validated_data)
        
        if expertise_required:
            project.expertise_required.set(expertise_required)
            
        is_published = validated_data.pop('is_published', False)
        
        if is_published:
            project.status = 'open'
    
        project.save()
        return project
    
    def update(self, instance, validated_data):
        expertise_required = validated_data.pop('expertise_required', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if expertise_required is not None:
            instance.expertise_required.set(expertise_required)
        
        instance.save()
        
        return instance
    
    
    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Deadline cannot be in the past")
        return value
    
    
class ProjectListSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    expertise_required_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'owner', 'owner_name', 'title', 'status', 'budget',
                  'deadline', 'expertise_required_names', 'created_at']
        
        read_only_fields = ['id', 'owner_name', 'expertise_required_names', 'created_at']
    
    def get_owner_name(self, obj):
        return obj.owner.full_name
    
    def get_expertise_required_names(self, obj):
        return [expertise.name for expertise in obj.expertise_required.all()]
    
        
    

    
    
    