🚀 Projet SUPRSS
SUPRSS est une application web de gestion de flux RSS, permettant de s’abonner, organiser et partager des collections de flux.

📋 Description
Application web complète avec base de données PostgreSQL, backend et frontend conteneurisés avec Docker.
🏗️ Architecture
suprss/
├── docker-compose.yml          # Orchestration des services
├── bd_suprss/                  # Scripts base de données
│   └── suprss_postgresql_schema.sql
├── backend/                    # [À venir] API backend
├── frontend/                   # [À venir] Interface utilisateur
└── README.md
✅ Étapes accomplies
Phase 1 : Base de données ✓

 Configuration PostgreSQL avec Docker
 Script SQL d'initialisation fonctionnel
 Volume persistant pour les données
 Réseau Docker pour la communication inter-services

Configuration actuelle

Base de données : PostgreSQL 15
Nom de la base : suprss_bd
Utilisateur : postgres
Port : 5432

🚀 Démarrage rapide
Prérequis

Docker et Docker Compose installés

Lancement
bash# Cloner le projet
git clone [URL_DU_REPO]
cd suprss

# Démarrer la base de données
docker compose up -d

# Vérifier les logs
docker logs suprss_postgres

# Se connecter à la base (optionnel)
docker exec -it suprss_postgres psql -U postgres -d suprss_bd