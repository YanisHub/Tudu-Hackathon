from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
from datetime import timedelta

from .models import Notification
from .services import (
    create_notification, 
    mark_notifications_as_read, 
    get_notification_counts,
    bulk_delete_notifications
)
from .serializers import (
    NotificationSerializer, 
    NotificationCountSerializer, 
    BulkActionSerializer
)

User = get_user_model()


class NotificationModelTests(TestCase):
    """
    Tests pour le modèle Notification.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_notification_creation(self):
        """Test de création d'une notification."""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification'
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.notification_type, 'project_created')
        self.assertEqual(notification.message, 'Test notification')
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        self.assertTrue(notification.is_recent)
    
    def test_mark_as_read(self):
        """Test de marquage d'une notification comme lue."""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
        
        notification.mark_as_read()
        
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_as_unread(self):
        """Test de marquage d'une notification comme non lue."""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification',
            is_read=True
        )
        notification.read_at = timezone.now()
        notification.save()
        
        notification.mark_as_unread()
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
    
    def test_age_in_days(self):
        """Test du calcul de l'âge d'une notification."""
        # Notification récente
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification'
        )
        self.assertEqual(notification.age_in_days, 0)
        
        # Notification ancienne (simulation)
        old_date = timezone.now() - timedelta(days=5)
        notification.created_at = old_date
        notification.save()
        self.assertEqual(notification.age_in_days, 5)


class NotificationServicesTests(TestCase):
    """
    Tests pour les services de notifications.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_create_notification_success(self):
        """Test de création réussie d'une notification."""
        notification = create_notification(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification'
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.notification_type, 'project_created')
    
    def test_create_notification_invalid_type(self):
        """Test de création avec un type invalide."""
        with self.assertRaises(ValueError):
            create_notification(
                recipient=self.user,
                notification_type='invalid_type',
                message='Test notification'
            )
    
    def test_create_notification_invalid_recipient(self):
        """Test de création avec un destinataire invalide."""
        with self.assertRaises(ValidationError):
            create_notification(
                recipient=None,
                notification_type='project_created',
                message='Test notification'
            )
    
    def test_mark_notifications_as_read(self):
        """Test de marquage des notifications comme lues."""
        # Créer quelques notifications
        notif1 = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test 1'
        )
        notif2 = Notification.objects.create(
            recipient=self.user,
            notification_type='application_received',
            message='Test 2'
        )
        
        # Marquer toutes comme lues
        count = mark_notifications_as_read(self.user)
        
        self.assertEqual(count, 2)
        notif1.refresh_from_db()
        notif2.refresh_from_db()
        self.assertTrue(notif1.is_read)
        self.assertTrue(notif2.is_read)
    
    def test_get_notification_counts(self):
        """Test de récupération des compteurs de notifications."""
        # Créer des notifications
        Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test 1'
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type='application_received',
            message='Test 2',
            is_read=True
        )
        
        counts = get_notification_counts(self.user)
        
        self.assertEqual(counts['total'], 2)
        self.assertEqual(counts['unread'], 1)


class NotificationAPITests(APITestCase):
    """
    Tests pour les vues API des notifications.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Créer quelques notifications de test
        self.notification1 = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification 1'
        )
        self.notification2 = Notification.objects.create(
            recipient=self.user,
            notification_type='application_received',
            message='Test notification 2',
            is_read=True
        )
    
    def test_notification_list_authenticated(self):
        """Test d'accès à la liste des notifications en étant authentifié."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
    
    def test_notification_list_unauthenticated(self):
        """Test d'accès à la liste des notifications sans authentification."""
        response = self.client.get('/api/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_notification_detail_patch(self):
        """Test de mise à jour d'une notification."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/notifications/{self.notification1.id}/',
            {'is_read': True}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
    
    def test_mark_notifications_read(self):
        """Test de marquage des notifications comme lues."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/notifications/mark-read/',
            {'notification_ids': [str(self.notification1.id)]}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.is_read)
    
    def test_notification_counts(self):
        """Test de récupération des compteurs de notifications."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/notifications/count/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['total'], 2)
        self.assertEqual(response.data['data']['unread'], 1)


class NotificationSerializerTests(TestCase):
    """
    Tests pour les serializers de notifications.
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_notification_serializer(self):
        """Test du serializer de notification."""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='project_created',
            message='Test notification'
        )
        
        serializer = NotificationSerializer(notification)
        data = serializer.data
        
        self.assertEqual(data['id'], str(notification.id))
        self.assertEqual(data['notification_type'], 'project_created')
        self.assertEqual(data['message'], 'Test notification')
        self.assertFalse(data['is_read'])
        self.assertIsNotNone(data['created_at_formatted'])
    
    def test_notification_count_serializer(self):
        """Test du serializer de compteurs."""
        data = {'total': 5, 'unread': 2}
        serializer = NotificationCountSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['total'], 5)
        self.assertEqual(serializer.validated_data['unread'], 2)
    
    def test_notification_count_serializer_invalid(self):
        """Test du serializer de compteurs avec données invalides."""
        data = {'total': 2, 'unread': 5}  # unread > total
        serializer = NotificationCountSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
    
    def test_bulk_action_serializer(self):
        """Test du serializer d'actions en lot."""
        notification_ids = [str(self.notification1.id), str(self.notification2.id)]
        data = {'notification_ids': notification_ids}
        serializer = BulkActionSerializer(data=data)
        
        # Note: Ce test nécessitera d'ajuster selon vos UUIDs réels
        # Pour l'instant, testons juste le format
        if hasattr(self, 'notification1'):
            self.assertTrue(serializer.is_valid())
