from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer
from .permissions import IsCollaboratorORProjectOwner
from projects.models import Project

# Import for notifications
from notifications.services import create_notification

# Import for standardization utilities
from utils.responses import api_response
from utils.error_handler import api_error_handler


class ChatSessionList(APIView):
    """
    API endpoint to list all chat sessions for the user.
    """
    permission_classes = [IsAuthenticated]
    
    @api_error_handler
    def get(self, request):
        """Get only chats where the user is owner or collaborator"""
        user = request.user
        chat_sessions = ChatSession.objects.filter(
            Q(project__owner=user) | Q(project__collaborator=user)
        ).select_related('project')
        
        serializer = ChatSessionSerializer(chat_sessions, many=True, context={'request': request})
        response_data, status_code = api_response(
            success=True,
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        return Response(response_data, status=status_code)


class ChatSessionDetail(APIView):
    """
    API endpoint to retrieve a specific chat session.
    """
    permission_classes = [IsAuthenticated]
    
    @api_error_handler
    def get(self, request, pk):
        """Retrieve a specific chat session"""
        try:
            user = request.user
            # Filter before calling get_object_or_404
            queryset = ChatSession.objects.filter(
                Q(project__owner=user) | Q(project__collaborator=user)
            )
            chat_session = get_object_or_404(queryset, pk=pk)
            
            serializer = ChatSessionSerializer(chat_session, context={'request': request})
            response_data, status_code = api_response(
                success=True,
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        except ChatSession.DoesNotExist:
            response_data, status_code = api_response(
                success=False,
                message='Chat session not found or access not authorized',
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            print(f"Unexpected error in ChatSessionDetail: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='An unexpected error occurred while retrieving the session',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)


class ChatMessageList(APIView):
    """
    API endpoint to list all messages in a chat session and add new ones.
    """
    permission_classes = [IsAuthenticated, IsCollaboratorORProjectOwner]
    
    @api_error_handler
    def get(self, request, chat_session_id):
        """Retrieve all messages from a chat session"""
        try:
            session = get_object_or_404(ChatSession, id=chat_session_id)
            
            # Check that the user has access to this chat
            self.check_object_permissions(request, session)
            
            # Mark unread messages as read
            ChatMessage.objects.filter(
                chat_session=session,
                is_read=False
            ).exclude(
                sender=request.user
            ).update(is_read=True)
            
            messages = ChatMessage.objects.filter(chat_session=session)
            serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
            response_data, status_code = api_response(
                success=True,
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )
            return Response(response_data, status=status_code)
            
        except ChatSession.DoesNotExist:
            response_data, status_code = api_response(
                success=False,
                message='Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            print(f"Unexpected error in ChatMessageList GET: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='An unexpected error occurred while retrieving messages',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)
    
    @api_error_handler
    def post(self, request, chat_session_id):
        """Create a new message in a chat session"""
        try:
            session = get_object_or_404(ChatSession, id=chat_session_id)
            
            # Check that the user has access to this chat
            self.check_object_permissions(request, session)
            
            # Validate message content
            content = request.data.get('content', '').strip()
            if not content:
                response_data, status_code = api_response(
                    success=False,
                    message='Message content is required',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)
            
            # Use atomic transaction to ensure consistency
            with transaction.atomic():
                # Create a new message
                message = ChatMessage.objects.create(
                    chat_session=session,
                    sender=request.user,
                    content=content
                )
                
                # Determine notification recipient
                project = session.project
                if request.user == project.owner:
                    recipient = project.collaborator
                else:
                    recipient = project.owner
                
                # Create notification for recipient
                if recipient:
                    create_notification(
                        recipient=recipient,
                        notification_type='new_message',
                        message=f"New message from {request.user.full_name or request.user.email} in project '{project.title}'",
                        related_object=message
                    )
                
                # Update session's last activity timestamp
                session.save()
                
                serializer = ChatMessageSerializer(message, context={'request': request})
                response_data, status_code = api_response(
                    success=True,
                    message='Message sent successfully',
                    data=serializer.data,
                    status_code=status.HTTP_201_CREATED
                )
                return Response(response_data, status=status_code)
                
        except ChatSession.DoesNotExist:
            response_data, status_code = api_response(
                success=False,
                message='Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            print(f"Unexpected error in ChatMessageList POST: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='An unexpected error occurred while sending the message',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)


class UploadAttachment(APIView):
    """
    API endpoint to upload an attachment for a message.
    """
    permission_classes = [IsAuthenticated, IsCollaboratorORProjectOwner]
    
    @api_error_handler
    def post(self, request, chat_session_id):
        """Upload an attachment for a chat message"""
        try:
            session = get_object_or_404(ChatSession, id=chat_session_id)
            
            # Check that the user has access to this chat
            self.check_object_permissions(request, session)
            
            # Check if a file was uploaded
            if 'attachment' not in request.FILES:
                response_data, status_code = api_response(
                    success=False,
                    message='No file was uploaded',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)
            
            file = request.FILES['attachment']
            
            # Create message with attachment
            message = ChatMessage.objects.create(
                chat_session=session,
                sender=request.user,
                content=f"Attachment: {file.name}",
                attachment=file
            )
            
            # Update session's last activity timestamp
            session.save()
            
            serializer = ChatMessageSerializer(message, context={'request': request})
            response_data, status_code = api_response(
                success=True,
                message='Attachment uploaded successfully',
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )
            return Response(response_data, status=status_code)
            
        except ChatSession.DoesNotExist:
            response_data, status_code = api_response(
                success=False,
                message='Chat session not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            print(f"Unexpected error in UploadAttachment: {str(e)}")
            response_data, status_code = api_response(
                success=False,
                message='An unexpected error occurred while uploading the attachment',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)
