from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PaymentTransaction
from projects.models import Project
from applications.models import Application
from .serializers import PaymentTransactionSerializer
from projects.permissions import IsProjectOwner
from projects.permissions import IsProjectOwnerOrCollaborator


class CreateEscrowPaymentView(APIView):
    """
    Endpoint to create and process a payment into escrow when a project owner 
    approves an applicant.
    """
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    @transaction.atomic
    def post(self, request, project_id, application_id):
        # Get project and verify ownership
        project = get_object_or_404(Project, id=project_id)
        self.check_object_permissions(request, project)
        
        # Get application and verify it's for this project
        application = get_object_or_404(
            Application, 
            id=application_id, 
            project=project, 
            status='pending'
        )
        
        # Check if payment transaction already exists
        if hasattr(project, 'payment_transaction'):
            return Response(
                {"detail": "Payment transaction already exists for this project."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create payment transaction record
        transaction = PaymentTransaction.objects.create(
            project=project,
            amount=project.budget,
            status='pending',
        )

        # Create a Stripe PaymentIntent for the escrow deposit
        from . import services
        intent = services.create_payment_intent(
            amount=project.budget,
            metadata={
                "project_id": str(project.id),
                "transaction_id": str(transaction.id),
            },
        )

        transaction.payment_provider = "stripe"
        transaction.transaction_id_provider = intent.id
        transaction.save(update_fields=["payment_provider", "transaction_id_provider"])
        
        # Update project status and assign collaborator
        project.status = 'in_progress'
        project.collaborator = application.applicant
        project.save()
        
        # Update application status
        application.status = 'accepted'
        application.save()
        
        # Reject other applications
        project.applications.exclude(id=application_id).update(status='rejected')
        
        serializer = PaymentTransactionSerializer(transaction)
        response_data = serializer.data
        response_data["client_secret"] = intent.client_secret
        return Response(response_data, status=status.HTTP_201_CREATED)


class ReleaseEscrowFundsView(APIView):
    """
    Endpoint for project owner to release funds from escrow to the collaborator
    once work is completed satisfactorily.
    """
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]

    @transaction.atomic
    def post(self, request, project_id):
        # Get project and verify ownership
        project = get_object_or_404(Project, id=project_id)
        self.check_object_permissions(request, project)
        
        # Get and verify payment transaction
        transaction = get_object_or_404(
            PaymentTransaction, 
            project=project,
            status='held'
        )
        
        # Capture the PaymentIntent to release the held funds
        from . import services

        try:
            services.capture_payment_intent(transaction.transaction_id_provider)
            transaction.release_funds()
            
            # Update project status
            project.status = 'completed'
            project.completed_at = timezone.now()
            project.save()
            
            serializer = PaymentTransactionSerializer(transaction)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RefundEscrowFundsView(APIView):
    """
    Endpoint for refunding escrow funds to the project owner.
    Could be used in case of disputes or project cancellation.
    Typically this would be an admin-only operation in case of disputes.
    """
    permission_classes = [permissions.IsAuthenticated, IsProjectOwner]  # In real app, might be admin-only
    
    @transaction.atomic
    def post(self, request, project_id):
        # Get project and verify ownership
        project = get_object_or_404(Project, id=project_id)
        self.check_object_permissions(request, project)
        
        # Get and verify payment transaction
        transaction = get_object_or_404(
            PaymentTransaction, 
            project=project,
            status='held'
        )
        
        # Refund through the payment provider
        from . import services

        try:
            services.refund_payment_intent(transaction.transaction_id_provider)
            transaction.refund_funds()
            
            # Update project status
            project.status = 'cancelled'
            project.save()
            
            serializer = PaymentTransactionSerializer(transaction)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentTransactionDetailView(generics.RetrieveAPIView):
    """
    Retrieve details about a specific payment transaction.
    Accessible to both project owner and collaborator.
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectOwnerOrCollaborator]
    
    def get_object(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        self.check_object_permissions(self.request, project)
        return get_object_or_404(PaymentTransaction, project=project)


class StripeWebhookView(APIView):
    """Handle Stripe webhook events."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from . import services

        event = services.construct_event(
            request.body, request.META.get("HTTP_STRIPE_SIGNATURE", "")
        )
        if event is None:
            return Response(status=400)

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type in [
            "payment_intent.succeeded",
            "payment_intent.amount_capturable_updated",
        ]:
            transaction_id = data.get("metadata", {}).get("transaction_id")
            if transaction_id:
                try:
                    txn = PaymentTransaction.objects.get(id=transaction_id)
                    if txn.status == "pending":
                        txn.mark_as_held()
                except PaymentTransaction.DoesNotExist:
                    pass
        elif event_type == "payment_intent.payment_failed":
            transaction_id = data.get("metadata", {}).get("transaction_id")
            if transaction_id:
                try:
                    txn = PaymentTransaction.objects.get(id=transaction_id)
                    txn.mark_as_failed()
                except PaymentTransaction.DoesNotExist:
                    pass

        return Response(status=200)
