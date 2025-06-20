from rest_framework import serializers
from .models import PaymentTransaction
from projects.serializers import ProjectSerializer


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for payment transactions with detailed project information.
    """
    project_details = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'project', 'project_details', 'amount', 'status', 'status_display',
            'created_at', 'paid_at', 'released_at', 'refunded_at',
            'payment_provider', 'transaction_id_provider'
        ]
        read_only_fields = ['id', 'created_at', 'paid_at', 'released_at', 'refunded_at']
    
    def get_project_details(self, obj):
        """
        Get detailed project information.
        """
        from projects.serializers import ProjectListSerializer
        return ProjectListSerializer(obj.project, context=self.context).data 