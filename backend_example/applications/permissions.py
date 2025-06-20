from rest_framework import permissions

class IsApplicationOwnerOrProjectOwner(permissions.BasePermission):
    """
    Permission to allow only the applicant or project owner
    to access an application.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is the applicant
        is_applicant = obj.applicant == request.user
        
        # Check if the user is the project owner
        is_project_owner = obj.project.owner == request.user
        
        return is_applicant or is_project_owner


class IsProjectOwner(permissions.BasePermission):
    """
    Permission to allow only the project owner to access a resource.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is the project owner
        return obj.project.owner == request.user


class IsApplicant(permissions.BasePermission):
    """
    Permission to allow only the applicant to access their own application.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is the applicant
        return obj.applicant == request.user
