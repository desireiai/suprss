# business_models/user_business.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import secrets

from models.user import Utilisateur, UtilisateurStatistiques
from dto.user_dto import (
    UserRegisterDTO,
    UserUpdateDTO,
    UserPreferencesDTO,
    UserStatsDTO
)
from core.security import (
    hash_password,
    verify_password,
    generate_email_verification_token,
    generate_password_reset_token,
    verify_email_verification_token,
    verify_password_reset_token,
    validate_password_strength
)
from core.email import EmailService

logger = logging.getLogger(__name__)

class UserBusiness:
    """Logique métier pour la gestion des utilisateurs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def create_user(self, user_data: UserRegisterDTO) -> Utilisateur:
        """Crée un nouvel utilisateur"""
        try:
            # Valider la force du mot de passe
            is_valid, error_msg = validate_password_strength(user_data.mot_de_passe)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Créer l'utilisateur
            user = Utilisateur(
                nom_utilisateur=user_data.nom_utilisateur,
                email=user_data.email,
                mot_de_passe_hash=hash_password(user_data.mot_de_passe),
                prenom=user_data.prenom,
                nom=user_data.nom,
                est_actif=True,
                email_verifie=False,
                mode_sombre=False,
                taille_police="medium",
                cree_le=datetime.utcnow()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Créer les statistiques initiales
            stats = UtilisateurStatistiques(
                utilisateur_id=user.id,
                total_articles_lus=0,
                total_favoris=0,
                total_flux=0,
                total_collections=0,
                total_commentaires=0
            )
            self.db.add(stats)
            
            # Créer la catégorie par défaut
            from business_models.category_business import CategoryBusiness
            category_business = CategoryBusiness(self.db)
            category_business.create_default_category(user.id)
            
            self.db.commit()
            
            logger.info(f"Utilisateur créé avec succès: {user.nom_utilisateur}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[Utilisateur]:
        """Authentifie un utilisateur"""
        try:
            user = self.db.query(Utilisateur).filter(
                Utilisateur.email == email,
                Utilisateur.est_actif == True,
                Utilisateur.supprime_le.is_(None)
            ).first()
            
            if not user:
                logger.warning(f"Tentative de connexion avec email inconnu: {email}")
                return None
            
            if not verify_password(password, user.mot_de_passe_hash):
                logger.warning(f"Mot de passe incorrect pour: {email}")
                return None
            
            # Vérifier si l'email est vérifié
            if not user.email_verifie:
                logger.warning(f"Email non vérifié pour: {email}")
                # On peut décider de permettre la connexion mais avec restrictions
            
            return user
            
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son ID"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.id == user_id,
            Utilisateur.supprime_le.is_(None)
        ).first()
    
    def get_user_by_email(self, email: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son email"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.email == email,
            Utilisateur.supprime_le.is_(None)
        ).first()
    
    def get_user_by_username(self, username: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.nom_utilisateur == username,
            Utilisateur.supprime_le.is_(None)
        ).first()
    
    def email_exists(self, email: str) -> bool:
        """Vérifie si un email existe déjà"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.email == email,
            Utilisateur.supprime_le.is_(None)
        ).first() is not None
    
    def username_exists(self, username: str) -> bool:
        """Vérifie si un nom d'utilisateur existe déjà"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.nom_utilisateur == username,
            Utilisateur.supprime_le.is_(None)
        ).first() is not None
    
    def update_user(self, user_id: int, user_update: UserUpdateDTO) -> Utilisateur:
        """Met à jour les informations d'un utilisateur"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            # Mettre à jour les champs fournis
            if user_update.nom_utilisateur:
                user.nom_utilisateur = user_update.nom_utilisateur
            if user_update.email:
                user.email = user_update.email
                user.email_verifie = False  # Réinitialiser la vérification
            if user_update.prenom is not None:
                user.prenom = user_update.prenom
            if user_update.nom is not None:
                user.nom = user_update.nom
            
            user.modifie_le = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Utilisateur {user_id} mis à jour")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
            raise
    
    def update_preferences(self, user_id: int, preferences: UserPreferencesDTO) -> Utilisateur:
        """Met à jour les préférences de l'utilisateur"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            if preferences.mode_sombre is not None:
                user.mode_sombre = preferences.mode_sombre
            if preferences.taille_police:
                user.taille_police = preferences.taille_police
            
            user.modifie_le = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour des préférences: {e}")
            raise
    
    def verify_password(self, user_id: int, password: str) -> bool:
        """Vérifie le mot de passe d'un utilisateur"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        return verify_password(password, user.mot_de_passe_hash)
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """Change le mot de passe d'un utilisateur"""
        try:
            # Valider la force du nouveau mot de passe
            is_valid, error_msg = validate_password_strength(new_password)
            if not is_valid:
                raise ValueError(error_msg)
            
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.mot_de_passe_hash = hash_password(new_password)
            user.modifie_le = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Mot de passe changé pour l'utilisateur {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du changement de mot de passe: {e}")
            raise
    
    def generate_reset_token(self, user_id: int) -> str:
        """Génère un token de réinitialisation de mot de passe"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        token = generate_password_reset_token(user.email, user.id)
        
        # Stocker le token dans la base de données ou Redis
        # Pour simplifier, on peut utiliser Redis avec une expiration
        from core.redis_client import redis_client
        redis_client.setex(
            f"password_reset:{token}",
            3600,  # 1 heure
            user.id
        )
        
        return token
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Réinitialise le mot de passe avec un token"""
        try:
            # Vérifier le token
            payload = verify_password_reset_token(token)
            if not payload:
                return False
            
            user_id = payload.get("user_id")
            if not user_id:
                return False
            
            # Changer le mot de passe
            return self.change_password(user_id, new_password)
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du mot de passe: {e}")
            return False
    
    def send_verification_email(self, email: str, user_id: int):
        """Envoie un email de vérification"""
        try:
            token = generate_email_verification_token(email, user_id)
            verification_url = f"https://suprss.com/verify-email?token={token}"
            
            self.email_service.send_email(
                to_email=email,
                subject="Vérifiez votre adresse email - SUPRSS",
                template="email_verification.html",
                context={
                    "verification_url": verification_url,
                    "expires_in": "24 heures"
                }
            )
            
            logger.info(f"Email de vérification envoyé à {email}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de vérification: {e}")
    
    def send_reset_password_email(self, email: str, token: str):
        """Envoie un email de réinitialisation de mot de passe"""
        try:
            reset_url = f"https://suprss.com/reset-password?token={token}"
            
            self.email_service.send_email(
                to_email=email,
                subject="Réinitialisation de votre mot de passe - SUPRSS",
                template="password_reset.html",
                context={
                    "reset_url": reset_url,
                    "expires_in": "1 heure"
                }
            )
            
            logger.info(f"Email de réinitialisation envoyé à {email}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation: {e}")
    
    def verify_email_with_token(self, token: str) -> bool:
        """Vérifie l'email avec un token"""
        try:
            payload = verify_email_verification_token(token)
            if not payload:
                return False
            
            user_id = payload.get("user_id")
            if not user_id:
                return False
            
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            user.email_verifie = True
            user.modifie_le = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Email vérifié pour l'utilisateur {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la vérification de l'email: {e}")
            return False
    
    def update_last_login(self, user_id: int):
        """Met à jour la dernière connexion de l'utilisateur"""
        try:
            user = self.get_user_by_id(user_id)
            if user:
                user.derniere_connexion = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la dernière connexion: {e}")
    
    def get_user_statistics(self, user_id: int) -> UserStatsDTO:
        """Récupère les statistiques de l'utilisateur"""
        stats = self.db.query(UtilisateurStatistiques).filter(
            UtilisateurStatistiques.utilisateur_id == user_id
        ).first()
        
        if not stats:
            # Créer des statistiques par défaut si elles n'existent pas
            stats = UtilisateurStatistiques(
                utilisateur_id=user_id,
                total_articles_lus=0,
                total_favoris=0,
                total_flux=0,
                total_collections=0,
                total_commentaires=0
            )
            self.db.add(stats)
            self.db.commit()
        
        return UserStatsDTO(
            total_articles_lus=stats.total_articles_lus,
            total_favoris=stats.total_favoris,
            total_flux=stats.total_flux,
            total_collections=stats.total_collections,
            total_commentaires=stats.total_commentaires
        )
    
    def soft_delete_user(self, user_id: int):
        """Supprime un utilisateur (soft delete)"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            user.supprime_le = datetime.utcnow()
            user.est_actif = False
            
            # Anonymiser les données personnelles
            user.email = f"deleted_{user_id}@suprss.com"
            user.nom_utilisateur = f"deleted_user_{user_id}"
            user.prenom = None
            user.nom = None
            
            self.db.commit()
            
            logger.info(f"Utilisateur {user_id} supprimé (soft delete)")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            raise
    
    def get_or_create_oauth_user(
        self,
        provider: str,
        email: str,
        nom_utilisateur: Optional[str] = None,
        prenom: Optional[str] = None,
        nom: Optional[str] = None
    ) -> Utilisateur:
        """Récupère ou crée un utilisateur OAuth"""
        try:
            # Vérifier si l'utilisateur existe déjà
            user = self.get_user_by_email(email)
            
            if user:
                # Mettre à jour les informations si nécessaire
                if prenom and not user.prenom:
                    user.prenom = prenom
                if nom and not user.nom:
                    user.nom = nom
                
                user.derniere_connexion = datetime.utcnow()
                self.db.commit()
                
                return user
            
            # Créer un nouvel utilisateur
            if not nom_utilisateur:
                # Générer un nom d'utilisateur unique
                base_username = email.split("@")[0]
                nom_utilisateur = base_username
                counter = 1
                
                while self.username_exists(nom_utilisateur):
                    nom_utilisateur = f"{base_username}{counter}"
                    counter += 1
            
            user = Utilisateur(
                nom_utilisateur=nom_utilisateur,
                email=email,
                mot_de_passe_hash=hash_password(secrets.token_urlsafe(32)),  # Mot de passe aléatoire
                prenom=prenom,
                nom=nom,
                est_actif=True,
                email_verifie=True,  # Email déjà vérifié par le provider OAuth
                mode_sombre=False,
                taille_police="medium",
                cree_le=datetime.utcnow(),
                derniere_connexion=datetime.utcnow()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Créer les statistiques et la catégorie par défaut
            stats = UtilisateurStatistiques(
                utilisateur_id=user.id,
                total_articles_lus=0,
                total_favoris=0,
                total_flux=0,
                total_collections=0,
                total_commentaires=0
            )
            self.db.add(stats)
            
            from business_models.category_business import CategoryBusiness
            category_business = CategoryBusiness(self.db)
            category_business.create_default_category(user.id)
            
            self.db.commit()
            
            logger.info(f"Utilisateur OAuth créé: {user.nom_utilisateur} via {provider}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de l'utilisateur OAuth: {e}")
            raise
    
    def validate_oauth2_token(self, provider: str, token: str) -> Optional[Dict[str, Any]]:
        """Valide un token OAuth2 avec le provider"""
        # Cette fonction devrait faire appel aux APIs des providers OAuth2
        # Pour l'exemple, on retourne des données mockées
        
        # Dans la vraie implémentation, on ferait quelque chose comme:
        # response = httpx.get(
        #     provider_config["userinfo_url"],
        #     headers={"Authorization": f"Bearer {token}"}
        # )
        # return response.json() if response.status_code == 200 else None
        
        return {
            "email": "user@example.com",
            "username": "oauth_user",
            "given_name": "John",
            "family_name": "Doe"
        }