from rest_framework import permissions



class IsCollaboratorORProjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        
        if obj.project.owner == request.user or obj.project.collaborator == request.user:
            return True
        
        return False