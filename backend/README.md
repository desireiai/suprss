# SUPRSS Backend - FastAPI

Backend API pour l'application SUPRSS - Système de gestion de flux RSS avec partage et collaboration.

## Technologies utilisées

- **FastAPI** - Framework web moderne et rapide pour Python
- **PostgreSQL** - Base de données relationnelle
- **Redis** - Cache et gestion des sessions
- **SQLAlchemy** - ORM Python
- **Pydantic** - Validation des données
- **Docker** - Conteneurisation
- **Celery** - Tâches asynchrones
- **JWT** - Authentification

## Prérequis

- Docker et Docker Compose
- Python 3.11+ (pour le développement local)
- Git

## Installation

### 1. Cloner le repository

```bash
git clone https://github.com/desireiai/suprss.git
cd suprss
```

### 2. Configuration de l'environnement

```bash
# Copier le fichier d'environnement exemple
cp .env.example .env

# Éditer le fichier .env avec vos configurations
nano .env
```

### 3. Démarrage avec Docker

```bash
# Construire et démarrer tous les services
docker-compose up -d

# Vérifier que tous les services sont démarrés
docker-compose ps

# Voir les logs
docker-compose logs -f backend
```

### 4. Accès aux services

- **API Backend**: http://localhost:8000
- **Documentation API (Swagger)**: http://localhost:8000/api/docs
- **Documentation API (ReDoc)**: http://localhost:8000/api/redoc
- **PgAdmin**: http://localhost:5050 (admin@suprss.com / admin)
- **Flower (Monitoring Celery)**: http://localhost:5555

## 📁 Structure du projet

```
backend/
├── core/               # Configuration et utilitaires
│   ├── config.py      # Configuration de l'application
│   ├── database.py    # Configuration de la base de données
│   ├── security.py    # Fonctions de sécurité
│   ├── redis_client.py# Client Redis
│   └── scheduler.py   # Planificateur de tâches
│
├── models/            # Modèles SQLAlchemy
│   ├── user.py       # Modèle utilisateur
│   ├── rss.py        # Modèles flux RSS
│   ├── category.py   # Modèle catégorie
│   ├── collection.py # Modèle collection
│   └── interaction.py# Modèles commentaires/messages
│
├── business_models/   # Logique métier
│   ├── user_business.py
│   ├── rss_business.py
│   ├── category_business.py
│   ├── collection_business.py
│   └── interaction_business.py
│
├── dto/              # Data Transfer Objects
│   ├── user_dto.py
│   ├── rss_dto.py
│   ├── category_dto.py
│   ├── collection_dto.py
│   └── interaction_dto.py
│
├── routers/          # Routes API
│   ├── user_router.py
│   ├── rss_router.py
│   ├── category_router.py
│   ├── collection_router.py
│   └── interaction_router.py
│
├── migrations/       # Migrations de base de données
├── tests/           # Tests unitaires et d'intégration a venir
├── static/          # Fichiers statiques
├── uploads/         # Fichiers uploadés
├── logs/            # Fichiers de logs
│
├── main.py          # Point d'entrée de l'application
├── Dockerfile       # Configuration Docker
├── requirements.txt # Dépendances Python
└── README.md       # Documentation
```

## 🔌 API Endpoints principaux

### Authentification
- `POST /api/users/register` - Inscription
- `POST /api/users/login` - Connexion
- `POST /api/users/refresh-token` - Rafraîchir le token
- `POST /api/users/password-reset/request` - Demander une réinitialisation

### Flux RSS
- `GET /api/rss/flux` - Liste des flux de l'utilisateur
- `POST /api/rss/flux` - Ajouter un flux
- `GET /api/rss/articles` - Liste des articles
- `PATCH /api/rss/articles/{id}/status` - Marquer lu/favori

### Catégories
- `GET /api/categories` - Liste des catégories
- `POST /api/categories` - Créer une catégorie
- `PUT /api/categories/{id}` - Modifier une catégorie

### Collections
- `GET /api/collections` - Liste des collections
- `POST /api/collections` - Créer une collection
- `POST /api/collections/{id}/members` - Ajouter un membre

### Interactions
- `POST /api/interactions/comments` - Ajouter un commentaire
- `POST /api/interactions/messages` - Envoyer un message
- `GET /api/interactions/notifications` - Récupérer les notifications

### Recherche
- `POST /api/search/global` - Recherche globale
- `GET /api/search/articles` - Recherche dans les articles

## 🔧 Développement

### Configuration locale (sans Docker)

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur de développement
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Génération des modèles depuis la base de données

```bash
# Utiliser sqlacodegen
docker run --rm --network suprss_network -v ${PWD}/backend:/app python:3.11-slim sh -c \
"pip install sqlacodegen psycopg2-binary && sqlacodegen postgresql://postgres:mypassword@postgres:5432/suprss_bd > /app/models/generated_models.py"
```

### Migrations de base de données

```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "Description de la migration"

# Appliquer les migrations
alembic upgrade head

# Revenir à une version précédente
alembic downgrade -1
```

## 📊 Monitoring

### Métriques disponibles

- `/health` - État de santé de l'application
- `/metrics` - Métriques Prometheus
- Flower UI pour Celery: http://localhost:5555

### Logs

Les logs sont stockés dans le dossier `logs/` et sont également visibles via Docker:

```bash
# Voir les logs du backend
docker-compose logs -f backend

# Voir les logs de tous les services
docker-compose logs -f
```

## Déploiement

### Variables d'environnement importantes pour la production

```bash
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<clé-secrète-très-longue-et-sécurisée>
DATABASE_URL=<url-de-production>
REDIS_URL=<url-redis-production>
```

### Build pour la production

```bash
# Build de l'image optimisée
docker build -t suprss-backend:latest -f Dockerfile.prod .

# Push vers un registry
docker tag suprss-backend:latest your-registry/suprss-backend:latest
docker push your-registry/suprss-backend:latest
```

## 🔒 Sécurité

- Authentification JWT avec tokens d'accès et de rafraîchissement
- Hachage des mots de passe avec bcrypt
- Validation des entrées avec Pydantic
- Protection CORS configurée
- Rate limiting sur les endpoints sensibles
- Soft delete pour préserver l'intégrité des données

## Fonctionnalités principales

- ✅ Gestion complète des utilisateurs (inscription, connexion, profil)
- ✅ Gestion des flux RSS avec parsing automatique
- ✅ Catégorisation personnalisée des flux
- ✅ Collections partagées avec système de permissions
- ✅ Commentaires sur articles avec support des réponses
- ✅ Chat en temps réel via WebSocket
- ✅ Système de notifications
- ✅ Recherche avancée avec filtres
- ✅ Import/Export OPML
- ✅ Statistiques utilisateur
- ✅ Mode sombre et préférences



## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Auteurs

- **MENSAH Yao Olivier Desire** - *Développeur principal* - [GitHub](https://github.com/desireiai)

## Remerciements

- SUPINFO pour le cadre du projet
- La communauté FastAPI pour l'excellent framework
- Tous les contributeurs open source

## Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Email : support@suprss.com

---

**SUPRSS** - Votre gestionnaire de flux RSS moderne et collaboratif 