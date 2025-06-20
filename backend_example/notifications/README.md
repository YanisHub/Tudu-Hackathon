# Application Notifications - Standardisation et Améliorations

## Vue d'ensemble

Cette application a été refactorisée pour suivre les mêmes patterns de standardisation et de gestion d'erreurs que l'application `accounts`. Les améliorations incluent une meilleure gestion des erreurs, des réponses API standardisées, et des fonctionnalités étendues.

## Améliorations apportées

### 1. Standardisation des réponses API

Toutes les vues utilisent maintenant la fonction `api_response()` de `utils.responses` pour garantir un format de réponse cohérent :

```python
response_data, status_code = api_response(
    success=True,
    message='Notification mise à jour avec succès',
    data=serializer.data,
    status_code=status.HTTP_200_OK
)
return Response(response_data, status=status_code)
```

### 2. Gestion centralisée des erreurs

- Utilisation du décorateur `@api_error_handler` sur toutes les vues
- Gestion appropriée des exceptions avec journalisation
- Messages d'erreur en français
- Validation robuste des données d'entrée

### 3. Améliorations du modèle

#### Nouveaux champs :
- `read_at` : Date et heure de lecture de la notification
- Help text en français pour tous les champs

#### Nouvelles méthodes :
- `mark_as_read()` : Marque une notification comme lue
- `mark_as_unread()` : Marque une notification comme non lue
- `is_recent` (property) : Vérifie si la notification est récente (< 24h)
- `age_in_days` (property) : Retourne l'âge en jours
- `get_related_object_info()` : Informations sur l'objet associé
- `get_unread_count_for_user()` (classmethod) : Compte les notifications non lues
- `mark_all_as_read_for_user()` (classmethod) : Marque toutes les notifications comme lues

#### Améliorations des index :
- Index sur `(recipient, is_read)`
- Index sur `(recipient, created_at)`
- Index sur `notification_type`

### 4. Services améliorés

#### Validation robuste :
- Vérification des types de paramètres
- Validation des types de notifications
- Gestion des erreurs avec `ValidationError`

#### Transactions atomiques :
- Toutes les opérations critiques utilisent `transaction.atomic()`

#### Nouveaux services :
- `delete_notification()` : Supprime une notification
- `bulk_delete_notifications()` : Supprime plusieurs notifications

### 5. Serializers enrichis

#### NotificationSerializer :
- Nouveau champ `read_at_formatted`
- Champs `is_recent` et `age_in_days`
- Email du destinataire
- Validation améliorée

#### Nouveaux serializers :
- `BulkActionSerializer` : Pour les actions en lot
- `NotificationCreateSerializer` : Pour la création (usage admin)

### 6. Nouvelles vues API

#### BulkDeleteNotificationsView :
- `DELETE /api/notifications/bulk-delete/`
- Suppression en lot de notifications
- Validation des données d'entrée

#### Améliorations des vues existantes :
- Méthodes helper pour réduire la duplication
- Gestion d'erreurs standardisée
- Messages d'erreur et de succès appropriés

### 7. Tests complets

Tests ajoutés pour :
- Modèles et leurs méthodes
- Services et leur validation
- API endpoints
- Serializers

## Structure des URLs

```python
urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-read/', views.MarkNotificationsReadView.as_view(), name='mark-notifications-read'),
    path('bulk-delete/', views.BulkDeleteNotificationsView.as_view(), name='bulk-delete-notifications'),
    path('count/', views.NotificationCountView.as_view(), name='notification-count'),
]
```

## Format de réponse standardisé

Toutes les réponses suivent le format :

```json
{
    "success": true|false,
    "message": "Message descriptif",
    "data": {...},
    "status_code": 200
}
```

## Exemples d'utilisation

### Marquer des notifications comme lues
```bash
POST /api/notifications/mark-read/
{
    "notification_ids": ["uuid1", "uuid2"]
}
```

### Supprimer des notifications en lot
```bash
DELETE /api/notifications/bulk-delete/
{
    "notification_ids": ["uuid1", "uuid2"]
}
```

### Mettre à jour une notification
```bash
PATCH /api/notifications/{uuid}/
{
    "is_read": true
}
```

## Gestion des erreurs

- Validation des données d'entrée avec messages explicites
- Gestion des permissions (utilisateur propriétaire uniquement)
- Journalisation des erreurs inattendues
- Codes de statut HTTP appropriés

## Migration nécessaire

Une nouvelle migration a été créée pour ajouter le champ `read_at` et les nouveaux index :

```bash
python manage.py migrate notifications
```

## Messages en français

Tous les messages utilisateur, types de notifications et documentation sont en français pour une meilleure expérience utilisateur.

## Cohérence avec l'application accounts

Cette refactorisation garantit une cohérence totale avec les patterns établis dans l'application `accounts`, facilitant la maintenance et l'évolution du code. 