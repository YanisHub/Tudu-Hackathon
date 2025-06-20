from django.urls import path
from . import views

urlpatterns = [
    # Create escrow payment when approving applicant
    path('projects/<uuid:project_id>/applications/<uuid:application_id>/pay/',
         views.CreateEscrowPaymentView.as_view(),
         name='escrow-payment-create'),
    
    # Release funds from escrow to collaborator
    path('projects/<uuid:project_id>/release-funds/',
         views.ReleaseEscrowFundsView.as_view(),
         name='escrow-release-funds'),
    
    # Refund funds from escrow to project owner (for disputes/cancellations)
    path('projects/<uuid:project_id>/refund-funds/',
         views.RefundEscrowFundsView.as_view(),
         name='escrow-refund-funds'),
    
    # Get transaction details
    path('projects/<uuid:project_id>/transaction/',
         views.PaymentTransactionDetailView.as_view(),
         name='payment-transaction-detail'),

    # Stripe webhook endpoint
    path('stripe/webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
]
