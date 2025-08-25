# business/user_business.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import secrets
import httpx

from models import Utilisateur, UtilisateurOauth, StatutUtilisateurArticle, Collection, Categorie, CommentaireArticle
from dtos.user_dto import (
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
    validate_password_strength
)

logger = logging.getLogger(__name__)

class UserBusiness:
    """Logique métier pour la gestion des utilisateurs"""
    
    def __init__(self, db: Session):
        self.db = db
        # Services optionnels - à injecter ou configurer selon votre architecture
        self.email_service = None
        self.redis_client = None
    
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
                cree_le=datetime.utcnow(),
                modifie_le=datetime.utcnow()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Créer la catégorie par défaut
            try:
                from business.category_business import CategoryBusiness
                category_business = CategoryBusiness(self.db)
                category_business.create_default_category(user.id)
            except ImportError:
                # Si CategoryBusiness n'existe pas encore, on peut créer une catégorie par défaut ici
                default_category = Categorie(
                    nom="Général",
                    utilisateur_id=user.id,
                    couleur="#007bff",
                    cree_le=datetime.utcnow()
                )
                self.db.add(default_category)
            
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
                Utilisateur.est_actif == True
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
            Utilisateur.est_actif == True
        ).first()
    
    def get_user_by_email(self, email: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son email"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.email == email,
            Utilisateur.est_actif == True
        ).first()
    
    def get_user_by_username(self, username: str) -> Optional[Utilisateur]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.nom_utilisateur == username,
            Utilisateur.est_actif == True
        ).first()
    
    def email_exists(self, email: str) -> bool:
        """Vérifie si un email existe déjà"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.email == email,
            Utilisateur.est_actif == True
        ).first() is not None
    
    def username_exists(self, username: str) -> bool:
        """Vérifie si un nom d'utilisateur existe déjà"""
        return self.db.query(Utilisateur).filter(
            Utilisateur.nom_utilisateur == username,
            Utilisateur.est_actif == True
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
        
        # Stocker le token dans la base de données
        user.token_reset_password = token
        user.token_reset_expire_le = datetime.utcnow() + timedelta(hours=1)
        
        self.db.commit()
        
        return token
    
    def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Réinitialise le mot de passe avec un token"""
        try:
            # Chercher l'utilisateur avec ce token
            user = self.db.query(Utilisateur).filter(
                Utilisateur.token_reset_password == token,
                Utilisateur.token_reset_expire_le > datetime.utcnow(),
                Utilisateur.est_actif == True
            ).first()
            
            if not user:
                logger.warning(f"Token de réinitialisation invalide ou expiré: {token}")
                return False
            
            # Changer le mot de passe
            is_valid, error_msg = validate_password_strength(new_password)
            if not is_valid:
                raise ValueError(error_msg)
            
            user.mot_de_passe_hash = hash_password(new_password)
            user.token_reset_password = None
            user.token_reset_expire_le = None
            user.modifie_le = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Mot de passe réinitialisé pour l'utilisateur {user.id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la réinitialisation du mot de passe: {e}")
            return False
    
    def send_verification_email(self, email: str, user_id: int):
        """Envoie un email de vérification"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return
            
            token = generate_email_verification_token(email, user_id)
            
            # Stocker le token dans la base de données
            user.token_verification_email = token
            user.modifie_le = datetime.utcnow()
            self.db.commit()
            
            if self.email_service:
                verification_url = f"https://suprss.com/verify-email/{token}"
                
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
            if self.email_service:
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
            user = self.db.query(Utilisateur).filter(
                Utilisateur.token_verification_email == token,
                Utilisateur.est_actif == True
            ).first()
            
            if not user:
                logger.warning(f"Token de vérification invalide: {token}")
                return False
            
            user.email_verifie = True
            user.email_verifie_le = datetime.utcnow()
            user.token_verification_email = None
            user.modifie_le = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Email vérifié pour l'utilisateur {user.id}")
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
        """Récupère les statistiques de l'utilisateur en calculant à la volée"""
        try:
            # Calculer les statistiques à partir des données existantes
            
            # Total d'articles lus
            total_articles_lus = self.db.query(func.count(StatutUtilisateurArticle.id)).filter(
                StatutUtilisateurArticle.utilisateur_id == user_id,
                StatutUtilisateurArticle.est_lu == True
            ).scalar() or 0
            
            # Total de favoris
            total_favoris = self.db.query(func.count(StatutUtilisateurArticle.id)).filter(
                StatutUtilisateurArticle.utilisateur_id == user_id,
                StatutUtilisateurArticle.est_favori == True
            ).scalar() or 0
            
            # Total de collections possédées
            total_collections = self.db.query(func.count(Collection.id)).filter(
                Collection.proprietaire_id == user_id
            ).scalar() or 0
            
            # Total de commentaires
            total_commentaires = self.db.query(func.count(CommentaireArticle.id)).filter(
                CommentaireArticle.utilisateur_id == user_id
            ).scalar() or 0
            
            # Total de flux (via les collections)
            total_flux = self.db.query(func.count(func.distinct('collection_flux.flux_id'))).select_from(
                Collection
            ).join(
                'collection_flux'
            ).filter(
                Collection.proprietaire_id == user_id
            ).scalar() or 0
            
            return UserStatsDTO(
                total_articles_lus=total_articles_lus,
                total_favoris=total_favoris,
                total_flux=total_flux,
                total_collections=total_collections,
                total_commentaires=total_commentaires
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            # Retourner des statistiques par défaut en cas d'erreur
            return UserStatsDTO(
                total_articles_lus=0,
                total_favoris=0,
                total_flux=0,
                total_collections=0,
                total_commentaires=0
            )
    
    def soft_delete_user(self, user_id: int):
        """Supprime un utilisateur (soft delete en désactivant)"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError("Utilisateur non trouvé")
            
            user.est_actif = False
            user.modifie_le = datetime.utcnow()
            
            # Anonymiser les données personnelles
            user.email = f"deleted_{user_id}@suprss.com"
            user.nom_utilisateur = f"deleted_user_{user_id}"
            user.prenom = None
            user.nom = None
            user.avatar_url = None
            
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
        provider_user_id: str,
        nom_utilisateur: Optional[str] = None,
        prenom: Optional[str] = None,
        nom: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> Utilisateur:
        """Récupère ou crée un utilisateur OAuth"""
        try:
            # Vérifier si l'utilisateur OAuth existe déjà
            oauth_user = self.db.query(UtilisateurOauth).filter(
                UtilisateurOauth.provider == provider,
                UtilisateurOauth.provider_user_id == provider_user_id
            ).first()
            
            if oauth_user:
                # Utilisateur OAuth existant
                user = oauth_user.utilisateur
                
                # Mettre à jour les informations si nécessaire
                if prenom and not user.prenom:
                    user.prenom = prenom
                if nom and not user.nom:
                    user.nom = nom
                
                # Mettre à jour les tokens OAuth
                oauth_user.access_token = access_token
                oauth_user.refresh_token = refresh_token
                oauth_user.derniere_utilisation = datetime.utcnow()
                
                user.derniere_connexion = datetime.utcnow()
                user.modifie_le = datetime.utcnow()
                
                self.db.commit()
                return user
            
            # Vérifier si un utilisateur avec cet email existe déjà
            user = self.get_user_by_email(email)
            
            if user:
                # Utilisateur existant, créer la liaison OAuth
                oauth_record = UtilisateurOauth(
                    utilisateur_id=user.id,
                    provider=provider,
                    provider_user_id=provider_user_id,
                    provider_email=email,
                    provider_username=nom_utilisateur,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    cree_le=datetime.utcnow(),
                    derniere_utilisation=datetime.utcnow()
                )
                
                self.db.add(oauth_record)
                user.derniere_connexion = datetime.utcnow()
                user.modifie_le = datetime.utcnow()
                
                self.db.commit()
                return user
            
            # Créer un nouvel utilisateur
            if not nom_utilisateur:
                # Générer un nom d'utilisateur unique
                base_username = email.split("@")[0] if email else f"{provider}_user"
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
                modifie_le=datetime.utcnow(),
                derniere_connexion=datetime.utcnow()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Créer l'enregistrement OAuth
            oauth_record = UtilisateurOauth(
                utilisateur_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=email,
                provider_username=nom_utilisateur,
                access_token=access_token,
                refresh_token=refresh_token,
                cree_le=datetime.utcnow(),
                derniere_utilisation=datetime.utcnow()
            )
            
            self.db.add(oauth_record)
            
            # Créer la catégorie par défaut
            try:
                from business.category_business import CategoryBusiness
                category_business = CategoryBusiness(self.db)
                category_business.create_default_category(user.id)
            except ImportError:
                default_category = Categorie(
                    nom="Général",
                    utilisateur_id=user.id,
                    couleur="#007bff",
                    cree_le=datetime.utcnow()
                )
                self.db.add(default_category)
            
            self.db.commit()
            
            logger.info(f"Utilisateur OAuth créé: {user.nom_utilisateur} via {provider}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de l'utilisateur OAuth: {e}")
            raise
    
    def validate_oauth2_token(self, provider: str, token: str) -> Optional[Dict[str, Any]]:
        """Valide un token OAuth2 avec le provider"""
        try:
            # Configuration des endpoints pour chaque provider
            provider_configs = {
                "google": {
                    "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                    "headers": {"Authorization": f"Bearer {token}"}
                },
                "microsoft": {
                    "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                    "headers": {"Authorization": f"Bearer {token}"}
                },
                "github": {
                    "userinfo_url": "https://api.github.com/user",
                    "headers": {"Authorization": f"token {token}"}
                }
            }
            
            config = provider_configs.get(provider.lower())
            if not config:
                logger.error(f"Provider OAuth non supporté: {provider}")
                return None
            
            # Faire appel à l'API du provider
            response = httpx.get(
                config["userinfo_url"],
                headers=config["headers"],
                timeout=10.0
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Normaliser les données selon le provider
                if provider.lower() == "google":
                    return {
                        "email": user_data.get("email"),
                        "username": user_data.get("email", "").split("@")[0],
                        "given_name": user_data.get("given_name"),
                        "family_name": user_data.get("family_name")
                    }
                elif provider.lower() == "microsoft":
                    return {
                        "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                        "username": user_data.get("displayName", "").replace(" ", "_").lower(),
                        "given_name": user_data.get("givenName"),
                        "family_name": user_data.get("surname")
                    }
                elif provider.lower() == "github":
                    return {
                        "email": user_data.get("email"),
                        "username": user_data.get("login"),
                        "given_name": user_data.get("name", "").split(" ")[0] if user_data.get("name") else None,
                        "family_name": " ".join(user_data.get("name", "").split(" ")[1:]) if user_data.get("name") and len(user_data.get("name", "").split(" ")) > 1 else None
                    }
                
            logger.warning(f"Échec de validation du token OAuth pour {provider}: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du token OAuth: {e}")
            return None