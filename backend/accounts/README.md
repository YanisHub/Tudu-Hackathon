# API Accounts - Documentation Technique

## Vue d'ensemble
Application Django REST Framework pour la gestion des utilisateurs, authentification JWT, gestion des profils et des expertises. Cette API fournit un système complet d'authentification avec vérification d'email, réinitialisation de mot de passe et gestion des compétences utilisateur.

## Modèles de données

### User (Utilisateur principal)
```python
{
    "id": "UUID (primary key)",
    "email": "string (unique, required)",
    "first_name": "string (required)",
    "last_name": "string (required)", 
    "is_staff": "boolean (default: false)",
    "is_superuser": "boolean (default: false)",
    "is_verified": "boolean (default: false)",
    "is_active": "boolean (default: true)",
    "date_joined": "datetime (auto)",
    "last_login": "datetime (auto)",
    "auth_provider": "string (email/google, default: email)"
}
```

### UserProfile (Profil utilisateur étendu)
```python
{
    "id": "UUID (primary key)",
    "user": "OneToOne relation to User",
    "bio": "text (optional)",
    "avatar": "ImageField (optional)",
    "has_onboarded": "boolean (default: false)",
    "verification_method_expertise": "string (optional)",
    "created_at": "datetime (auto)",
    "updated_at": "datetime (auto)"
}
```

### ExpertiseArea (Domaines d'expertise)
```python
{
    "id": "UUID (primary key)",
    "name": "string (required)",
    "parent": "ForeignKey to self (optional, hiérarchie)",
    "created_at": "datetime (auto)"
}
```

### UserExpertise (Liaison utilisateur-expertise)
```python
{
    "id": "UUID (primary key)",
    "user": "ForeignKey to User",
    "expertise": "ForeignKey to ExpertiseArea",
    "proficiency_level": "integer (1-5, default: 3)",
    "is_verified": "boolean (default: false)",
    "created_at": "datetime (auto)",
    "updated_at": "datetime (auto)"
}
```

## Endpoints API

### Base URL: `/api/accounts/`

### Authentification & Inscription

#### POST `/register/`
**Description:** Inscription d'un nouvel utilisateur
**Auth:** Non requis
**Body:**
```json
{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe", 
    "password": "MotDePasse123!",
    "password2": "MotDePasse123!"
}
```
**Validation mot de passe:**
- Min 6 caractères
- Au moins une majuscule
- Au moins un chiffre  
- Au moins un caractère spécial (!@#$%^&*())

**Response 201:**
```json
{
    "success": true,
    "message": "Merci pour votre inscription. Un code de vérification a été envoyé à votre adresse email",
    "data": {
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

#### POST `/verify-email/`
**Description:** Vérification de l'email avec code OTP
**Auth:** Non requis
**Body:**
```json
{
    "otp": "123456"
}
```
**Response 200:**
```json
{
    "success": true,
    "message": "Email vérifié avec succès"
}
```

#### POST `/login/`
**Description:** Connexion utilisateur
**Auth:** Non requis
**Body:**
```json
{
    "email": "user@example.com",
    "password": "MotDePasse123!"
}
```
**Response 200:**
```json
{
    "success": true,
    "message": "Connexion réussie",
    "data": {
        "email": "user@example.com",
        "full_name": "John Doe",
        "access_token": "jwt_access_token_here",
        "refresh_token": "jwt_refresh_token_here"
    }
}
```

#### POST `/logout/`
**Description:** Déconnexion utilisateur (blacklist du refresh token)
**Auth:** Required (Bearer token)
**Body:**
```json
{
    "refresh_token": "jwt_refresh_token_here"
}
```

#### POST `/token/refresh/`
**Description:** Renouvellement du token d'accès
**Auth:** Non requis
**Body:**
```json
{
    "refresh": "jwt_refresh_token_here"
}
```

### Réinitialisation de mot de passe

#### POST `/password-reset/`
**Description:** Demande de réinitialisation de mot de passe
**Auth:** Non requis
**Body:**
```json
{
    "email": "user@example.com"
}
```

#### GET `/password-reset-confirm/<uidb64>/<token>/`
**Description:** Validation du lien de réinitialisation
**Auth:** Non requis

#### PATCH `/set-new-password/`
**Description:** Définition du nouveau mot de passe
**Auth:** Non requis
**Body:**
```json
{
    "password": "NouveauMotDePasse123!",
    "confirm_password": "NouveauMotDePasse123!",
    "uidb64": "encoded_user_id",
    "token": "reset_token"
}
```

### Gestion des profils

#### GET `/current-user/`
**Description:** Récupération des données complètes de l'utilisateur connecté
**Auth:** Required (Bearer token)
**Response 200:**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": "uuid",
            "email": "user@example.com",
            "full_name": "John Doe",
            "is_active": true,
            "is_staff": false,
            "date_joined": "2024-01-01T00:00:00Z",
            "profile": {
                "bio": "Developer passionate about...",
                "has_onboarded": true,
                "avatar": "http://example.com/media/avatars/image.jpg"
            }
        },
        "expertise": [
            {
                "id": "uuid",
                "expertise_details": {
                    "id": "uuid",
                    "name": "JavaScript",
                    "parent": null
                },
                "proficiency_level": 4,
                "is_verified": false
            }
        ]
    }
}
```

#### GET `/profile/`
**Description:** Récupération du profil utilisateur
**Auth:** Required (Bearer token)
**Response 200:**
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "bio": "Developer passionate about...",
        "avatar": "http://example.com/media/avatars/image.jpg",
        "has_onboarded": true,
        "verification_method_expertise": "portfolio",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z"
    }
}
```

#### PUT/PATCH `/profile/`
**Description:** Mise à jour du profil utilisateur
**Auth:** Required (Bearer token)
**Body (multipart/form-data pour avatar):**
```json
{
    "bio": "Updated bio text",
    "has_onboarded": true,
    "avatar": "file_upload"
}
```

#### DELETE `/profile/`
**Description:** Suppression du profil utilisateur
**Auth:** Required (Bearer token)

### Gestion des expertises

#### GET `/expertise-areas/`
**Description:** Liste des domaines d'expertise disponibles
**Auth:** Required (Bearer token)
**Query params:**
- `search`: Recherche textuelle
- `ordering`: Tri (name, created_at)

**Response 200:**
```json
{
    "success": true,
    "data": {
        "count": 50,
        "next": "http://api/accounts/expertise-areas/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "name": "JavaScript",
                "parent": null,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
    }
}
```

#### POST `/expertise-areas/create/`
**Description:** Création d'un nouveau domaine d'expertise (Admin uniquement)
**Auth:** Required (Admin Bearer token)
**Body:**
```json
{
    "name": "React",
    "parent": "uuid_of_javascript_if_subcategory"
}
```

#### GET/PUT/PATCH/DELETE `/expertise-areas/<uuid>/`
**Description:** Opérations CRUD sur un domaine d'expertise spécifique
**Auth:** Required (Admin pour modifications)

#### GET `/available-expertise/`
**Description:** Domaines d'expertise non encore ajoutés par l'utilisateur
**Auth:** Required (Bearer token)

#### GET `/user-expertise/`
**Description:** Liste des expertises de l'utilisateur connecté
**Auth:** Required (Bearer token)
**Response 200:**
```json
{
    "success": true,
    "data": [
        {
            "id": "uuid",
            "expertise_details": {
                "id": "uuid",
                "name": "JavaScript",
                "parent": null,
                "created_at": "2024-01-01T00:00:00Z"
            },
            "proficiency_level": 4,
            "is_verified": false,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z"
        }
    ]
}
```

#### POST `/user-expertise/`
**Description:** Ajout d'une expertise à l'utilisateur
**Auth:** Required (Bearer token)
**Body:**
```json
{
    "expertise": "uuid_of_expertise_area",
    "proficiency_level": 4
}
```

#### GET/PUT/PATCH/DELETE `/user-expertise/<uuid>/`
**Description:** Opérations CRUD sur une expertise utilisateur spécifique
**Auth:** Required (Bearer token, propriétaire uniquement)

## Authentification

### JWT Token Format
- **Access Token:** Durée de vie courte (15-30 minutes)
- **Refresh Token:** Durée de vie longue (7 jours)
- **Header:** `Authorization: Bearer <access_token>`

### Permissions
- **IsAuthenticated:** Utilisateur connecté requis
- **IsAdminUser:** Utilisateur admin requis  
- **IsOwnerOrReadOnly:** Propriétaire pour modifications, lecture libre

## Gestion des erreurs

### Codes d'erreur standard
- **400:** Bad Request (données invalides)
- **401:** Unauthorized (token manquant/invalide)
- **403:** Forbidden (permissions insuffisantes)
- **404:** Not Found (ressource inexistante)
- **500:** Internal Server Error

### Format de réponse d'erreur
```json
{
    "success": false,
    "message": "Description de l'erreur",
    "errors": {
        "field_name": ["Message d'erreur spécifique"]
    }
}
```

## Validation des données

### Email
- Format email valide
- Unique dans le système

### Mot de passe
- Minimum 6 caractères
- Au moins une majuscule
- Au moins un chiffre
- Au moins un caractère spécial

### Proficiency Level (Niveau d'expertise)
- Entier entre 1 et 5
- 1: Débutant, 2: Novice, 3: Intermédiaire, 4: Avancé, 5: Expert

## Fonctionnalités spéciales

### Système OTP
- Code de vérification de 6 chiffres
- Hashage sécurisé avec sel
- Expiration après 15 minutes
- Suppression automatique après usage

### Hiérarchie des expertises
- Support des catégories parent/enfant
- Permet l'organisation en arbre des compétences

### Upload d'avatar
- Support des images (JPEG, PNG)
- Stockage dans `media/avatars/`
- URL complète retournée dans les réponses

## Notes pour le développement Frontend

### États d'authentification à gérer
1. **Non connecté:** Afficher login/register
2. **Connecté non vérifié:** Demander code OTP  
3. **Connecté vérifié non onboardé:** Processus d'onboarding
4. **Connecté complet:** Accès à toutes les fonctionnalités

### Persistance des tokens
- Stocker refresh token de manière sécurisée
- Renouveler automatiquement l'access token
- Gérer la déconnexion sur expiration

### Interface utilisateur suggérée
1. **Page d'inscription:** Email, nom, prénom, mot de passe
2. **Page de vérification:** Saisie code OTP
3. **Page de connexion:** Email, mot de passe
4. **Dashboard utilisateur:** Profil + expertises
5. **Gestion du profil:** Bio, avatar, onboarding
6. **Gestion des expertises:** Ajout/suppression/modification niveau 