from django.db import models
import uuid
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from projects.models import Project


class PaymentTransaction(models.Model):
    """
    Represents the payment transaction and escrow status for a project.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending Payment')), # Initial state before client pays
        ('held', _('Held in Escrow')),    # Client paid, funds held
        ('released', _('Released to Collaborator')), # Project completed, funds released
        ('refunded', _('Refunded to Client')), # Project cancelled or disputed
        ('failed', _('Payment Failed'))      # Initial payment attempt failed
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(Project, on_delete=models.PROTECT, related_name='payment_transaction',
                                 help_text=_("Associated project for this transaction"))
    # Amount can be directly sourced from project.budget_amount if always the same
    amount = models.DecimalField(max_digits=10, decimal_places=2, 
                               help_text=_("Transaction amount, usually the project budget"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps for tracking status changes
    created_at = models.DateTimeField(auto_now_add=True) # When the transaction record was created
    paid_at = models.DateTimeField(null=True, blank=True) # When the client successfully paid into escrow
    released_at = models.DateTimeField(null=True, blank=True) # When funds were released to collaborator
    refunded_at = models.DateTimeField(null=True, blank=True) # When funds were refunded to client
    
    # Optional: Fields for storing payment provider details (e.g., Stripe charge ID)
    payment_provider = models.CharField(max_length=50, blank=True, null=True)
    transaction_id_provider = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"Transaction for {self.project.title} - Status: {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']
        
    def mark_as_held(self):
        """
        Mark transaction as successfully held in escrow.
        Called after successful payment processing.
        """
        self.status = 'held'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])
        return self
        
    def release_funds(self):
        """
        Release funds to collaborator.
        Called when project is completed successfully.
        """
        if self.status != 'held':
            raise ValueError("Can only release funds that are currently held in escrow")
            
        self.status = 'released'
        self.released_at = timezone.now()
        self.save(update_fields=['status', 'released_at'])
        return self
        
    def refund_funds(self):
        """
        Refund funds to project owner.
        Called when project is cancelled or in case of dispute.
        """
        if self.status != 'held':
            raise ValueError("Can only refund funds that are currently held in escrow")
            
        self.status = 'refunded'
        self.refunded_at = timezone.now()
        self.save(update_fields=['status', 'refunded_at'])
        return self
        
    def mark_as_failed(self):
        """
        Mark transaction as failed.
        Called when payment processing fails.
        """
        self.status = 'failed'
        self.save(update_fields=['status'])
        return self
        
    @property
    def is_in_escrow(self):
        """
        Check if funds are currently held in escrow.
        """
        return self.status == 'held'
        
    @property
    def is_completed(self):
        """
        Check if transaction is completed (either released or refunded).
        """
        return self.status in ['released', 'refunded']
