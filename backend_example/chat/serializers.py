from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import ChatSession, ChatMessage
from projects.models import Project

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'avatar']
    
    def get_full_name(self, obj):
        return obj.full_name or obj.email
    
    def get_avatar(self, obj):
        """Get avatar from user profile"""
        try:
            if hasattr(obj, 'profile') and obj.profile and obj.profile.avatar:
                return obj.profile.avatar.url
            return None
        except Exception:
            return None


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserBriefSerializer(read_only=True)
    is_own_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'content', 'timestamp', 'is_read', 'attachment', 'is_own_message']
    
    def get_is_own_message(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.sender == request.user
        return False


class ChatSessionSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    project_title = serializers.CharField(source='project.title', read_only=True)
    other_user = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'project', 'project_title', 'created_at', 'updated_at', 
                 'latest_message', 'unread_count', 'other_user']
    
    def get_latest_message(self, obj):
        latest_message = obj.messages.order_by('-timestamp').first()
        if latest_message:
            return {
                'content': latest_message.content[:50] + '...' if len(latest_message.content) > 50 else latest_message.content,
                'timestamp': latest_message.timestamp,
                'sender': latest_message.sender.full_name or latest_message.sender.email,
                'has_attachment': bool(latest_message.attachment)
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if obj.project.owner == request.user:
                other_user = obj.project.collaborator
            else:
                other_user = obj.project.owner
            
            if other_user:
                return UserBriefSerializer(other_user).data
        return None
