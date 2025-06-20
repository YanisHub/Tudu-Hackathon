from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import uuid

from .models import PaymentTransaction
from projects.models import Project
from applications.models import Application

User = get_user_model()


class PaymentTransactionModelTest(TestCase):
    def setUp(self):
        # Create users
        self.project_owner = User.objects.create_user(username='owner', email='owner@test.com', password='password')
        self.collaborator = User.objects.create_user(username='collab', email='collab@test.com', password='password')
        
        # Create project
        self.project = Project.objects.create(
            owner=self.project_owner,
            title="Test Project",
            description="Test Description",
            budget=Decimal('1000.00'),
            deadline=timezone.now() + timezone.timedelta(days=30)
        )
        
    def test_payment_transaction_creation(self):
        transaction = PaymentTransaction.objects.create(
            project=self.project,
            amount=self.project.budget,
            status='pending'
        )
        
        self.assertEqual(transaction.project, self.project)
        self.assertEqual(transaction.amount, self.project.budget)
        self.assertEqual(transaction.status, 'pending')
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNone(transaction.paid_at)
        self.assertIsNone(transaction.released_at)
        self.assertIsNone(transaction.refunded_at)


class EscrowPaymentAPITest(APITestCase):
    def setUp(self):
        # Create users
        self.project_owner = User.objects.create_user(username='owner', email='owner@test.com', password='password')
        self.collaborator = User.objects.create_user(username='collab', email='collab@test.com', password='password')
        self.other_user = User.objects.create_user(username='other', email='other@test.com', password='password')
        
        # Create project
        self.project = Project.objects.create(
            owner=self.project_owner,
            title="Test Project",
            description="Test Description",
            budget=Decimal('1000.00'),
            deadline=timezone.now() + timezone.timedelta(days=30),
            status='open'
        )
        
        # Create application
        self.application = Application.objects.create(
            project=self.project,
            applicant=self.collaborator,
            cover_letter="I'd like to work on this project.",
            status='pending'
        )
        
        # URLs
        self.create_payment_url = reverse('escrow-payment-create', 
                                          kwargs={'project_id': self.project.id, 
                                                  'application_id': self.application.id})
        self.release_funds_url = reverse('escrow-release-funds', 
                                         kwargs={'project_id': self.project.id})
        self.refund_funds_url = reverse('escrow-refund-funds', 
                                        kwargs={'project_id': self.project.id})
        self.transaction_detail_url = reverse('payment-transaction-detail', 
                                             kwargs={'project_id': self.project.id})
        
    def test_create_escrow_payment_requires_auth(self):
        response = self.client.post(self.create_payment_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_create_escrow_payment_requires_project_owner(self):
        # Login as non-owner
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self.create_payment_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_create_escrow_payment_success(self):
        # Login as project owner
        self.client.force_authenticate(user=self.project_owner)
        response = self.client.post(self.create_payment_url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify transaction created
        self.assertTrue(PaymentTransaction.objects.filter(project=self.project).exists())
        transaction = PaymentTransaction.objects.get(project=self.project)
        self.assertEqual(transaction.amount, self.project.budget)
        self.assertEqual(transaction.status, 'pending')
        self.assertIsNone(transaction.paid_at)
        
        # Verify project updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'in_progress')
        self.assertEqual(self.project.collaborator, self.collaborator)
        
        # Verify application updated
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'accepted')

    def test_webhook_marks_transaction_held(self):
        self.client.force_authenticate(user=self.project_owner)
        self.client.post(self.create_payment_url)

        transaction = PaymentTransaction.objects.get(project=self.project)
        payload = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "metadata": {"transaction_id": str(transaction.id)}
                }
            },
        }
        response = self.client.post(
            reverse('stripe-webhook'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'held')
        
    def test_release_escrow_funds(self):
        # Create initial transaction
        transaction = PaymentTransaction.objects.create(
            project=self.project,
            amount=self.project.budget,
            status='held',
            paid_at=timezone.now()
        )
        
        # Login as project owner
        self.client.force_authenticate(user=self.project_owner)
        response = self.client.post(self.release_funds_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaction updated
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'released')
        self.assertIsNotNone(transaction.released_at)
        
        # Verify project updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'completed')
        self.assertIsNotNone(self.project.completed_at)
        
    def test_refund_escrow_funds(self):
        # Create initial transaction
        transaction = PaymentTransaction.objects.create(
            project=self.project,
            amount=self.project.budget,
            status='held',
            paid_at=timezone.now()
        )
        
        # Login as project owner
        self.client.force_authenticate(user=self.project_owner)
        response = self.client.post(self.refund_funds_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaction updated
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, 'refunded')
        self.assertIsNotNone(transaction.refunded_at)
        
        # Verify project updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'cancelled')
        
    def test_view_transaction_details(self):
        # Create transaction
        transaction = PaymentTransaction.objects.create(
            project=self.project,
            amount=self.project.budget,
            status='held',
            paid_at=timezone.now()
        )
        
        # Both owner and collaborator should be able to view details
        # Test as owner
        self.client.force_authenticate(user=self.project_owner)
        response = self.client.get(self.transaction_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test as collaborator
        self.project.collaborator = self.collaborator
        self.project.save()
        self.client.force_authenticate(user=self.collaborator)
        response = self.client.get(self.transaction_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test as other user
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.transaction_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
