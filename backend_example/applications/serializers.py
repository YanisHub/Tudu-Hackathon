from rest_framework import serializers


from accounts.serializers import UserSerializer
from projects.serializers import ProjectSerializer

from .models import Application


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for validating application status updates.
    Used only for validating input data.
    """
    STATUS_CHOICES = [
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    status = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        required=True,
        error_messages={
            'required': 'Status is required',
            'invalid_choice': 'Status must be "accepted" or "rejected"'
        }
    )


class ApplicationWithdrawSerializer(serializers.Serializer):
    """
    Serializer for validating application withdrawals.
    Allows for future extensions like withdrawal reason.
    """
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Optional reason for application withdrawal"
    )
    
    def validate_reason(self, value):
        """Optional reason validation"""
        if value and len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Reason must contain at least 3 characters"
            )
        return value.strip() if value else None


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_details = UserSerializer(source = 'applicant', read_only = True)
    project_details = serializers.SerializerMethodField()
    
    class Meta:
        
        model = Application
        fields = ['id', 'project', 'project_details', 'applicant', 'applicant_details',
                  'cover_letter', 'status', 'applied_at', 'updated_at']
        read_only_fields = ['id', 'status', 'applied_at', 'updated_at', 'applicant']
    
    def get_project_details(self, obj):
        return ProjectSerializer(obj.project, context=self.context).data
    
    
    
class ApplicationSIMPLESerialiazer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'project', 'applicant', 'cover_letter', 
                  'status', 'applied_at', 'updated_at']
        read_only_fields = ['id', 'status', 'applied_at', 'updated_at']
    
            
        
    
class ApplicationListSerializer(serializers.ModelSerializer):
    applicant_name = serializers.SerializerMethodField()
    
    class Meta:
        
        model = Application
        fields = ['id', 'project', 'applicant_name', 'applicant', 
                  'status', 'applied_at', 'updated_at']
        read_only_fields = ['id', 'status', 'applied_at', 'updated_at', 'applicant']
    
    def get_applicant_name(self, obj):
        return obj.applicant.full_name