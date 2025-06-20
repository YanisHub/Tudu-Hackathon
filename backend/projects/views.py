# Django imports
from django.db.models import Q
from django.shortcuts import get_object_or_404

# Django REST Framework imports
from rest_framework import permissions, filters, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

# Django Filters imports
from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet, NumberFilter, 
    CharFilter, DateFilter, ModelMultipleChoiceFilter
)

# Utils imports for standardized responses and error handling
from utils.responses import api_response
from utils.error_handler import api_error_handler

# Local imports
from .models import Project, ProjectAttachment
from .serializers import (
    ProjectSerializer, ProjectListSerializer, 
    ProjectAttachmentSerializer, ProjectAttachmentSimpleSerializer
)
from .permissions import (
    CanViewProject, IsProjectOwnerOrCollaborator, 
    CanModifyProject
)

# External app imports
from accounts.models import ExpertiseArea
from applications.models import Application

# --- Filters --- 

class ProjectStatusFilter(FilterSet):
    status = CharFilter(field_name="status", lookup_expr='iexact')
    class Meta:
        model = Project
        fields = ['status']

class ProjectMarketplaceFilter(FilterSet):
    min_budget = NumberFilter(field_name="budget", lookup_expr='gte')
    max_budget = NumberFilter(field_name="budget", lookup_expr='lte')
    deadline_before = DateFilter(field_name="deadline", lookup_expr='lte')
    deadline_after = DateFilter(field_name="deadline", lookup_expr='gte')
    expertise_required = ModelMultipleChoiceFilter(
        field_name='expertise_required__id',
        to_field_name='id',
        queryset=ExpertiseArea.objects.all(),
        conjoined=False # Use OR logic for multiple expertise areas (optional, set True for AND)
    )

    class Meta:
        model = Project
        fields = ['min_budget', 'max_budget', 'deadline_before', 'deadline_after', 'expertise_required']


# --- Base Project List View (for reuse) --- 

class BaseProjectListView(generics.ListAPIView):
    """ Base class for project lists with status filtering. """
    serializer_class = ProjectListSerializer # Use the lighter serializer for lists
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectStatusFilter # Allow filtering by status

    def get_base_queryset(self):
        raise NotImplementedError("Subclasses must implement get_base_queryset")

    def get_queryset(self):
        queryset = self.get_base_queryset()
        # Further filtering (like status) is handled by DjangoFilterBackend
        return queryset

    @api_error_handler
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            response_data, status_code = api_response(
                success=True, 
                data=paginated_response.data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)

        serializer = self.get_serializer(queryset, many=True)
        response_data, status_code = api_response(
            success=True, 
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)

# --- Specific User Project Lists --- 

class MyOwnedProjectsListView(BaseProjectListView):
    """ Lists projects owned by the current authenticated user. """
    def get_base_queryset(self):
        return Project.objects.filter(owner=self.request.user)

class MyCollaboratingProjectsListView(BaseProjectListView):
    """ Lists projects where the current authenticated user is the collaborator. """
    def get_base_queryset(self):
        return Project.objects.filter(collaborator=self.request.user)

class MyAppliedProjectsListView(BaseProjectListView):
    """ Lists projects the current authenticated user has applied to. """
    def get_base_queryset(self):
        # Get IDs of projects the user has applied to
        applied_project_ids = Application.objects.filter(
            applicant=self.request.user
        ).values_list('project_id', flat=True)
        
        # Return the Project objects for those IDs
        return Project.objects.filter(id__in=applied_project_ids)


# --- Marketplace View --- 

class ProjectMarketplaceListView(generics.ListAPIView):
    """ Lists projects open for applications (marketplace view) with advanced filtering and pagination. """
    serializer_class = ProjectListSerializer
    permission_classes = [permissions.IsAuthenticated] # Or AllowAny if public marketplace
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectMarketplaceFilter
    search_fields = ['title', 'description', 'expertise_required__name'] # Allow text search
    ordering_fields = ['created_at', 'deadline', 'budget']
    ordering = ['-created_at'] # Default ordering
    pagination_class = PageNumberPagination # Enable pagination
    # pagination_class.page_size = 10 # Optional: Set default page size

    def get_queryset(self):
        # Only show projects with status 'open' in the marketplace
        # and that are not owned by the user
        return Project.objects.filter(status='open').exclude(owner=self.request.user)

    @api_error_handler
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            response_data, status_code = api_response(
                success=True, 
                data=paginated_response.data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)

        serializer = self.get_serializer(queryset, many=True)
        response_data, status_code = api_response(
            success=True, 
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


# --- Project CRUD Views --- 

class ProjectCreateView(generics.CreateAPIView):
    """ Allows authenticated users to create a new project. """
    serializer_class = ProjectSerializer # Use the detail serializer for creation
    permission_classes = [permissions.IsAuthenticated]

    @api_error_handler
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        response_data, status_code = api_response(
            success=True,
            message="Projet créé avec succès",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
        return Response(response_data, status=status_code, headers=headers)

    def perform_create(self, serializer):
        # Set the owner to the current user automatically
        serializer.save(owner=self.request.user)

class ProjectDetailView(generics.RetrieveAPIView):
    """ Retrieves details of a specific project. """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer # Use the detail serializer
    permission_classes = [permissions.IsAuthenticated, CanViewProject]
    lookup_field = 'pk' # Or 'id' if using UUIDs in URL

    @api_error_handler
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)

class ProjectModifyView(generics.RetrieveUpdateDestroyAPIView):
    """ Allows the owner to retrieve, update, or delete a project if its status is draft or open. """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, CanModifyProject]
    lookup_field = 'pk'

    @api_error_handler
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)

    @api_error_handler
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        
        response_data, status_code = api_response(
            success=True,
            message="Projet mis à jour avec succès",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)

    @api_error_handler
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        
        response_data, status_code = api_response(
            success=True,
            message="Projet supprimé avec succès",
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)


# --- Project Attachment Views --- 

class ProjectAttachmentListCreateView(generics.ListCreateAPIView):
    """ Lists attachments for a specific project or creates a new attachment. """
    permission_classes = [permissions.IsAuthenticated, IsProjectOwnerOrCollaborator] 

    def get_serializer_class(self):
        """
        Utilise ProjectAttachmentSerializer pour les opérations de liste (GET)
        et ProjectAttachmentSimpleSerializer pour la création (POST).
        """
        if self.request.method == 'POST':
            return ProjectAttachmentSimpleSerializer
        return ProjectAttachmentSerializer

    def get_queryset(self):
        """
        Filters attachments based on the project_pk URL parameter.
        Ensures user has permission to view the project.
        """
        project_pk = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_pk)
        
        # Check if user can view the project (owner or collaborator)
        # The IsProjectOwnerOrCollaborator permission already handles this check 
        # based on the project object, but an explicit check adds clarity.
        if not (project.owner == self.request.user or project.collaborator == self.request.user):
             # This case should ideally be blocked by permissions, but good as a safeguard
             return ProjectAttachment.objects.none()

        return ProjectAttachment.objects.filter(project=project)

    def perform_create(self, serializer):
        """
        Sets the project based on the URL and the uploader as the current user.
        Permission check ensures user is owner/collaborator of the target project.
        """
        project_pk = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_pk)
        
        serializer.save()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_pk = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_pk)
        context.update({
            'request': self.request,
            'project': project
        })
        return context
        
    @api_error_handler
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
        
    @api_error_handler
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        response_data, status_code = api_response(
            success=True,
            message="Pièce jointe créée avec succès",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
        return Response(response_data, status=status_code, headers=headers)


class ProjectAttachmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """ Retrieves, updates, or deletes a specific project attachment. """
    permission_classes = [permissions.IsAuthenticated, IsProjectOwnerOrCollaborator]
    lookup_url_kwarg = 'attachment_pk' # The URL keyword argument for the attachment ID

    def get_serializer_class(self):
        """
        Utilise ProjectAttachmentSerializer pour les opérations de consultation (GET)
        et ProjectAttachmentSimpleSerializer pour la mise à jour (PUT/PATCH).
        """
        if self.request.method in ['PUT', 'PATCH']:
            return ProjectAttachmentSimpleSerializer
        return ProjectAttachmentSerializer

    def get_queryset(self):
        """
        Filters based on both project_pk and attachment_pk from URL.
        Ensures the attachment belongs to the specified project.
        """
        project_pk = self.kwargs.get('project_pk')
        attachment_pk = self.kwargs.get('attachment_pk')
        
        # Check if project exists (implicitly checks user access via permissions later)
        get_object_or_404(Project, pk=project_pk)
        
        return ProjectAttachment.objects.filter(project_id=project_pk, pk=attachment_pk)

    def get_object(self):
        """
        Override get_object to use the queryset filtered by project and attachment pk.
        Object-level permissions (IsProjectOwnerOrCollaborator) will be checked against this object.
        """
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        self.check_object_permissions(self.request, obj) # Explicitly check object permissions
        return obj

    def get_serializer_context(self):
        context = super().get_serializer_context()
        project_pk = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, pk=project_pk)
        context.update({
            'request': self.request,
            'project': project
        })
        return context
        
    @api_error_handler
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
        
    @api_error_handler
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Dans le cas d'une mise à jour, nous devons gérer manuellement le remplacement du fichier
        # car nous utilisons un sérialiseur simplifié
        if 'file' in serializer.validated_data:
            new_file = serializer.validated_data['file']
            instance.file = new_file
            instance.file_name = new_file.name
            instance.file_size = new_file.size
            instance.save()
        
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        
        # Utiliser le sérialiseur complet pour la réponse
        response_serializer = ProjectAttachmentSerializer(instance)
        
        response_data, status_code = api_response(
            success=True,
            message="Pièce jointe mise à jour avec succès",
            data=response_serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
        
    @api_error_handler
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        
        response_data, status_code = api_response(
            success=True,
            message="Pièce jointe supprimée avec succès",
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)
