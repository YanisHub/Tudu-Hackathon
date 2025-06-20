from rest_framework.views import APIView
from rest_framework.serializers import ValidationError
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

# Imports for response standardization and error handling
from utils.responses import api_response
from utils.error_handler import api_error_handler

from .serializers import (
    ApplicationSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationWithdrawSerializer,
)

from .models import Application
from projects.models import Project
from .permissions import (
    IsApplicationOwnerOrProjectOwner,
    IsProjectOwner,
    IsApplicant
)

# Import for automatic chat creation
from chat.models import ChatSession, ChatMessage

# Import for notifications
from notifications.services import create_notification


class ApplicationListCreateView(ListCreateAPIView):
    """
    List all applications or create a new application for a project.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter applications based on user role"""
        user = self.request.user
        # Return applications for projects owned by the user or applications submitted by the user
        return Application.objects.filter(project__owner=user) | Application.objects.filter(applicant=user)
    
    @api_error_handler
    def list(self, request, *args, **kwargs):
        """List all applications with standardized response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data, status_code = api_response(
                success=True,
                message="Applications retrieved successfully",
                data=self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        serializer = self.get_serializer(queryset, many=True)
        response_data, status_code = api_response(
            success=True,
            message="Applications retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def create(self, request, *args, **kwargs):
        """Create a new application with standardized response and validation"""
        project_id = request.data.get('project')
        
        if not project_id:
            response_data, status_code = api_response(
                success=False,
                message="Project ID is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        try:
            project = get_object_or_404(Project, id=project_id)
        except:
            response_data, status_code = api_response(
                success=False,
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        
        # Check that the user is not the project owner
        if project.owner == request.user:
            response_data, status_code = api_response(
                success=False,
                message="You cannot apply to your own project",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Check that the project is open for applications
        if project.status != 'open':
            response_data, status_code = api_response(
                success=False,
                message="This project is not currently accepting applications",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Check that an application doesn't already exist
        existing_application = Application.objects.filter(
            project=project, 
            applicant=request.user
        ).first()
        
        if existing_application:
            response_data, status_code = api_response(
                success=False,
                message="You have already applied to this project",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Create the application
        application = serializer.save(applicant=request.user, status='pending')
        
        # Create a notification for the project owner
        create_notification(
            recipient=project.owner,
            notification_type='application_received',
            message=f"New application from {request.user.full_name or request.user.email} for your project '{project.title}'",
            related_object=application
        )
        
        response_data, status_code = api_response(
            success=True,
            message="Application created successfully",
            data=ApplicationSerializer(application).data,
            status_code=status.HTTP_201_CREATED
        )
        return Response(response_data, status=status_code)


class ApplicationDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an application instance.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Application.objects.all()
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.request.method == 'GET':
            # For GET: applicant OR project owner can view
            permission_classes = [IsAuthenticated, IsApplicationOwnerOrProjectOwner]
        else:
            # For PUT/PATCH/DELETE: only the applicant can modify/delete
            permission_classes = [IsAuthenticated, IsApplicant]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Ensure that users can only see applications they've made or 
        applications for projects they own
        """
        user = self.request.user
        return Application.objects.filter(applicant=user) | Application.objects.filter(project__owner=user)
    
    @api_error_handler
    def retrieve(self, request, *args, **kwargs):
        """Retrieve an application with standardized response"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data, status_code = api_response(
            success=True,
            message="Application retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def update(self, request, *args, **kwargs):
        """Update an application with standardized response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check that the application can be modified
        if instance.status in ['accepted', 'rejected', 'withdrawn']:
            response_data, status_code = api_response(
                success=False,
                message=f"Cannot modify an application that is {instance.status}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        serializer.save()
        response_data, status_code = api_response(
            success=True,
            message="Application updated successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)
    
    @api_error_handler
    def destroy(self, request, *args, **kwargs):
        """Delete an application with standardized response"""
        instance = self.get_object()
        
        # Check that the application can be deleted
        if instance.status in ['accepted', 'rejected']:
            response_data, status_code = api_response(
                success=False,
                message=f"Cannot delete an application that is {instance.status}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        instance.delete()
        response_data, status_code = api_response(
            success=True,
            message="Application deleted successfully",
            status_code=status.HTTP_204_NO_CONTENT
        )
        return Response(response_data, status=status_code)


class ApplicationStatusUpdateView(GenericAPIView):
    """
    Update the status of an application (accept/reject).
    Only project owners can update the status.
    """
    serializer_class = ApplicationStatusUpdateSerializer
    permission_classes = [IsAuthenticated, IsProjectOwner]
    
    @api_error_handler
    def post(self, request, pk, *args, **kwargs):
        """Update application status with comprehensive validation and standardized response"""
        try:
            application = get_object_or_404(Application, id=pk)
        except:
            response_data, status_code = api_response(
                success=False,
                message="Application not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        
        # Check permissions
        self.check_object_permissions(request, application)
        
        # Validate input data with dedicated serializer
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        new_status = serializer.validated_data['status']
        
        # Prevent status update if already accepted or rejected or withdrawn
        if application.status in ['accepted', 'rejected', 'withdrawn']:
            response_data, status_code = api_response(
                success=False,
                message=f"Cannot update status of an application that is already {application.status}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
            
        if new_status == 'accepted':
            project = application.project
            
            # Check that the project doesn't already have a collaborator
            if project.collaborator:
                response_data, status_code = api_response(
                    success=False,
                    message="This project already has an assigned collaborator",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)
            
            project.collaborator = application.applicant
            project.status = 'in_progress'
            project.save()
            
            # Direct chat creation
            chat_session, created = ChatSession.objects.get_or_create(project=project)
            if created:
                ChatMessage.objects.create(
                    chat_session=chat_session,
                    sender=request.user,
                    content=f"Welcome! The application for the project '{project.title}' has been accepted. You can now discuss project details here."
                )
            
            # Notifications for the accepted applicant
            create_notification(
                recipient=application.applicant,
                notification_type='application_accepted',
                message=f"Your application for the project '{project.title}' has been accepted!",
                related_object=application
            )
            
            create_notification(
                recipient=application.applicant,
                notification_type='project_assigned',
                message=f"You are now a collaborator on the project '{project.title}'",
                related_object=project
            )
            
        elif new_status == 'rejected':
            # Notification for the rejected applicant
            create_notification(
                recipient=application.applicant,
                notification_type='application_rejected',
                message=f"Your application for the project '{application.project.title}' has been rejected",
                related_object=application
            )
        
        application.status = new_status
        application.save()
        
        response_data, status_code = api_response(
            success=True,
            message=f"Application {new_status} successfully",
            data=ApplicationSerializer(application).data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class WithdrawApplicationView(GenericAPIView):
    """
    Allow an applicant to withdraw their application.
    """
    serializer_class = ApplicationWithdrawSerializer
    permission_classes = [IsAuthenticated, IsApplicant]
    
    @api_error_handler
    def post(self, request, pk, *args, **kwargs):
        """Withdraw an application with comprehensive validation and standardized response"""
        try:
            application = get_object_or_404(Application, id=pk)
        except:
            response_data, status_code = api_response(
                success=False,
                message="Application not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        
        # Check permissions
        self.check_object_permissions(request, application)
        
        # Validate input data with dedicated serializer
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            response_data, status_code = api_response(
                success=False,
                message=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        # Get optional reason
        withdraw_reason = serializer.validated_data.get('reason')
        
        # Prevent withdrawing if already accepted or rejected or withdrawn
        if application.status in ['accepted', 'rejected', 'withdrawn']:
            response_data, status_code = api_response(
                success=False,
                message=f"Cannot withdraw an application that is already {application.status}",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        application.status = 'withdrawn'
        application.save()
        
        # Build notification message with reason if provided
        notification_message = f"The application from {application.applicant.full_name or application.applicant.email} for your project '{application.project.title}' has been withdrawn"
        if withdraw_reason:
            notification_message += f" (Reason: {withdraw_reason})"
        
        # Notification for the project owner
        create_notification(
            recipient=application.project.owner,
            notification_type='application_status_update',
            message=notification_message,
            related_object=application
        )
        
        response_data, status_code = api_response(
            success=True,
            message="Application withdrawn successfully",
            data=ApplicationSerializer(application).data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class UserApplicationsView(ListAPIView):
    """
    List all applications made by the current user with filtering by status
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        status = self.request.query_params.get('status')
        if status:
            return Application.objects.filter(applicant=self.request.user, status=status)
        return Application.objects.filter(applicant=self.request.user)
    
    @api_error_handler
    def list(self, request, *args, **kwargs):
        """List user applications with standardized response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data, status_code = api_response(
                success=True,
                message="User applications retrieved successfully",
                data=self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        serializer = self.get_serializer(queryset, many=True)
        response_data, status_code = api_response(
            success=True,
            message="User applications retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class ProjectApplicationsView(ListAPIView):
    """
    List all applications for a specific project.
    Only accessible by the project owner.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsProjectOwner]
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        try:
            project = get_object_or_404(Project, id=project_id)
        except:
            return Application.objects.none()
        
        # Ensure only the project owner can see all applications
        if project.owner != self.request.user:
            return Application.objects.none()
        
        return Application.objects.filter(project=project)
    
    @api_error_handler
    def list(self, request, *args, **kwargs):
        """List project applications with standardized response and validation"""
        project_id = self.kwargs.get('project_id')
        
        if not project_id:
            response_data, status_code = api_response(
                success=False,
                message="Project ID is required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        
        try:
            project = get_object_or_404(Project, id=project_id)
        except:
            response_data, status_code = api_response(
                success=False,
                message="Project not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        
        # Ensure only the project owner can see all applications
        if project.owner != request.user:
            response_data, status_code = api_response(
                success=False,
                message="You don't have permission to view applications for this project",
                status_code=status.HTTP_403_FORBIDDEN
            )
            return Response(response_data, status=status_code)
        
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data, status_code = api_response(
                success=True,
                message="Project applications retrieved successfully",
                data=self.get_paginated_response(serializer.data).data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        serializer = self.get_serializer(queryset, many=True)
        response_data, status_code = api_response(
            success=True,
            message="Project applications retrieved successfully",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)