from rest_framework import permissions
from .models import Project  # Assurez-vous que Project est importé


class IsProjectOwnerOrCollaborator(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est le propriétaire ou le collaborateur du projet.
    """
    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, 'project') else obj # Handle Project or ProjectAttachement

        if not project or not hasattr(project, 'owner') or not hasattr(project, 'collaborator'):
             return False # Safety check if object is not as expected

        # Allow owner or collaborator
        is_owner = request.user == project.owner
        is_collaborator = project.collaborator is not None and request.user == project.collaborator
        
        return is_owner or is_collaborator


class IsProjectOwner(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur est le propriétaire de l'objet (Projet ou Attachement lié).
    """
    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, 'project') else obj # Handle Project or ProjectAttachement

        if not project or not hasattr(project, 'owner'):
             return False # Safety check

        return project.owner == request.user
        


class CanViewProject(permissions.BasePermission):
    """
    Permission pour déterminer si un utilisateur peut voir un projet.
    Propriétaire, collaborateur peuvent voir. Tout le monde peut voir si statut 'open'.
    """
    
    def has_object_permission(self, request, view, obj):
        # Assumes obj is a Project instance
        if not isinstance(obj, Project):
             return False # Should only apply to Project objects

        # Project owner can always view
        if obj.owner == request.user:
            return True
            
        # Collaborator can view
        if obj.collaborator is not None and obj.collaborator == request.user:
            return True
            
        # If project is open, any authenticated user can view (adjust if needed)
        if obj.status == 'open' and request.user and request.user.is_authenticated:
            return True
            
        # Staff/admin can view (optional, add if needed)
        # if request.user.is_staff:
        #     return True

        return False 


class CanModifyProject(permissions.BasePermission):
    """
    Permission pour vérifier si l'utilisateur peut modifier ou supprimer un projet.
    Seul le propriétaire peut, et uniquement si le statut est 'draft' ou 'open'.
    """
    def has_object_permission(self, request, view, obj):
        # Assumes obj is a Project instance
        if not isinstance(obj, Project):
             return False 

        # Check if the user is the owner
        is_owner = obj.owner == request.user
        
        # Check if the status allows modification
        is_modifiable_status = obj.status in ['draft', 'open']
        
        return is_owner and is_modifiable_status 