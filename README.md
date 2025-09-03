# SUPRSS - Système Unifié de Partage RSS

Une application web moderne de gestion et partage de flux RSS avec interface React et API FastAPI.

## 🚀 Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Git

### Installation

1. **Cloner le projet**
```bash
git clone https://github.com/desireiai/suprss.git
cd suprss
```

2. **Configuration des environnements**
```bash
# Copier les fichiers d'environnement
cp .env.example .env
cp frontend/.env.example frontend/.env  
cp backend/.env.example backend/.env

# Éditer les fichiers selon vos besoins
nano .env
nano frontend/.env
nano backend/.env
```

3. **Nettoyer Docker (optionnel)**
```bash
docker-compose down
docker container prune -f
docker image prune -a -f
docker volume prune -f
docker network prune -f
```

4. **Construire et lancer l'application**
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🌐 Accès aux services

- **Frontend (React)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentation API**: http://localhost:8000/api/docs
- **PgAdmin**: http://localhost:5050 (admin@suprss.com / admin)
- **Monitoring Celery**: http://localhost:5555

## 📁 Structure du projet

```
suprss/
├── frontend/          # Application React
├── backend/           # API FastAPI
├── docker-compose.yml # Configuration Docker
├── .env              # Variables globales
└── README.md         # Ce fichier
```

## 🔧 Commandes utiles

```bash
# Voir les logs
docker-compose logs -f

# Arrêter l'application
docker-compose down

# Redémarrer un service
docker-compose restart backend
docker-compose restart frontend

# Accéder au conteneur backend
docker-compose exec backend bash
```

## 📖 Documentation

- [Frontend](frontend/README.md) - Documentation React
- [Backend](backend/README.md) - Documentation API FastAPI

## ⚡ Fonctionnalités

- ✅ Gestion complète des flux RSS
- ✅ Interface moderne et responsive
- ✅ Collections partagées
- ✅ Commentaires et interactions
- ✅ Recherche avancée
- ✅ Authentification JWT
- ✅ Mode temps réel (WebSocket)

## 🐛 Support

Pour toute question :
- Ouvrir une issue GitHub
- Email : support@suprss.com

---
**Développé par MENSAH Yao Olivier Desire**