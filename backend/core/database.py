# core/database.py
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Configuration du moteur de base de données
engine = create_engine(
    settings.get_database_url_sync(),
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycler les connexions après 1 heure
    echo=settings.DEBUG,  # Log SQL queries en mode debug
    future=True
)

# Configuration de la session
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# Métadonnées pour la création des tables
metadata = MetaData()

# Base pour les modèles SQLAlchemy
Base = declarative_base(metadata=metadata)

# Dependency pour obtenir une session de base de données
def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour obtenir une session de base de données.
    Ferme automatiquement la session après utilisation.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Erreur dans la transaction de base de données: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Fonction pour créer toutes les tables
def create_tables():
    """Crée toutes les tables dans la base de données"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables créées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la création des tables: {e}")
        raise

# Fonction pour supprimer toutes les tables
def drop_tables():
    """Supprime toutes les tables de la base de données"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Tables supprimées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des tables: {e}")
        raise

# Fonction pour vérifier la connexion à la base de données
def check_database_connection() -> bool:
    """Vérifie que la connexion à la base de données est fonctionnelle"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Connexion à la base de données réussie")
        return True
    except Exception as e:
        logger.error(f"Erreur de connexion à la base de données: {e}")
        return False

# Context manager pour les transactions
class DatabaseTransaction:
    """Context manager pour gérer les transactions de base de données"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise
        self.db.close()

# Fonction pour exécuter des requêtes SQL brutes
def execute_raw_sql(query: str, params: dict = None):
    """Exécute une requête SQL brute"""
    with engine.connect() as conn:
        result = conn.execute(query, params or {})
        conn.commit()
        return result

# Fonction pour obtenir les statistiques de la base de données
def get_database_stats() -> dict:
    """Récupère les statistiques de la base de données"""
    stats = {}
    
    with engine.connect() as conn:
        # Taille de la base de données
        result = conn.execute(
            f"SELECT pg_database_size('{settings.POSTGRES_DB}') as size"
        )
        stats['database_size'] = result.fetchone()['size']
        
        # Nombre de connexions actives
        result = conn.execute(
            "SELECT count(*) as connections FROM pg_stat_activity"
        )
        stats['active_connections'] = result.fetchone()['connections']
        
        # Tables et leur taille
        result = conn.execute("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """)
        stats['tables'] = [dict(row) for row in result]
    
    return stats