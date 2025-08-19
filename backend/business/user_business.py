# business/user_business.py
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from ..models.user import Utilisateur, UtilisateurOAuth
from ..models.category import Categorie, FluxCategorie
from ..models.collection import Collection, MembreCollection
from ..models.interaction import StatutUtilisateurArticle, CommentaireArticle
import bcrypt
import secrets
import re
import logging
import httpx
import jwt
from jwt import PyJWKClient

# Configuration du logger
logger = logging.getLogger(__name__)

class UserBusiness:
    """Logique métier pour la gestion des utilisateurs"""
    
    # Configuration OAuth2 pour les différents providers
    OAUTH_CONFIGS = {
        'google': {
            'userinfo_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'token_url': 'https://oauth2.googleapis.com/token',
            'jwks_url': 'https://www.googleapis.com/oauth2/v3/certs',
            'issuer': 'https://accounts.google.com'
        },
        'microsoft': {
            'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
            'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'jwks_url': 'https://login.microsoftonline.com/common/discovery/v2.0/keys',
            'issuer': 'https://login.microsoftonline.com'
        },
        'github': {
            'userinfo_url': 'https://api.github.com/user',
            'email_url': 'https://api.github.com/user/emails',
            'token_url': None,  # GitHub utilise directement le token
            'jwks_url': None,
            'issuer': None
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, 
                   nom_utilisateur: str,
                   email: str,
                   mot_de_passe: Optional[str] = None,
                   prenom: Optional[str] = None,
                   nom: Optional[str] = None,
                   is_oauth: bool = False) -> Utilisateur:
        """
        Créer un nouvel utilisateur avec validation
        
        Args:
            nom_utilisateur: Nom d'utilisateur unique
            email: Email de l'utilisateur
            mot_de_passe: Mot de passe (optionnel pour OAuth)
            prenom: Prénom de l'utilisateur
            nom: Nom de famille
            is_oauth: Si True, création via OAuth (pas de mot de passe requis)
        """
        
        # Validation
        if not self._validate_email(email):
            raise ValueError("Format d'email invalide")
        
        # Pour OAuth, on ne valide pas le mot de passe
        if not is_oauth:
            if not mot_de_passe:
                raise ValueError("Le mot de passe est requis pour une inscription standard")
            
            if not self._validate_password(mot_de_passe):
                raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        
        if not self._validate_username(nom_utilisateur):
            raise ValueError("Le nom d'utilisateur doit contenir entre 3 et 50 caractères alphanumériques")
        
        # Vérifier l'unicité
        if self.get_by_email(email):
            raise ValueError("Cet email est déjà utilisé")
        
        if self.get_by_username(nom_utilisateur):
            raise ValueError("Ce nom d'utilisateur est déjà pris")
        
        # Hasher le mot de passe si fourni
        password_hash = None
        if mot_de_passe:
            password_hash = bcrypt.hashpw(mot_de_passe.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Créer l'utilisateur
        user = Utilisateur(
            nom_utilisateur=nom_utilisateur,
            email=email,
            mot_de_passe_hash=password_hash,
            prenom=prenom,
            nom=nom,
            token_verification_email=self._generate_token() if not is_oauth else None,
            email_verifie=is_oauth,  # Email vérifié automatiquement pour OAuth
            email_verifie_le=datetime.utcnow() if is_oauth else None
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Créer une catégorie par défaut
        self._create_default_category(user.id)
        
        # Créer une collection personnelle par défaut
        self._create_default_collection(user.id)
        
        logger.info(f"Nouvel utilisateur créé: {nom_utilisateur} (ID: {user.id}, OAuth: {is_oauth})")
        
        return user
    
    def authenticate(self, email: str, mot_de_passe: str) -> Optional[Utilisateur]:
        """Authentifier un utilisateur avec email/mot de passe"""
        user = self.get_by_email(email)
        
        if not user or not user.est_actif:
            return None
        
        if not user.mot_de_passe_hash:
            # Peut-être un compte OAuth uniquement
            logger.warning(f"Tentative de connexion par mot de passe pour un compte OAuth: {email}")
            return None
        
        if bcrypt.checkpw(mot_de_passe.encode('utf-8'), 
                         user.mot_de_passe_hash.encode('utf-8')):
            # Mettre à jour la dernière connexion
            user.derniere_connexion = datetime.utcnow()
            self.db.commit()
            return user
        
        return None
    
    def authenticate_oauth(self, 
                         provider: str,
                         access_token: str,
                         id_token: Optional[str] = None) -> Tuple[Utilisateur, bool]:
        """
        Authentifier ou créer un utilisateur via OAuth2
        
        Args:
            provider: Le provider OAuth ('google', 'microsoft', 'github')
            access_token: Le token d'accès OAuth
            id_token: Le token ID (optionnel, utilisé par certains providers)
        
        Returns:
            Tuple (Utilisateur, is_new_user)
        
        Raises:
            ValueError: Si le provider n'est pas supporté ou si l'authentification échoue
        """
        
        provider = provider.lower()
        
        if provider not in self.OAUTH_CONFIGS:
            raise ValueError(f"Provider OAuth non supporté: {provider}")
        
        try:
            # Récupérer les informations utilisateur depuis le provider
            user_info = self._get_oauth_user_info(provider, access_token, id_token)
            
            if not user_info.get('email'):
                raise ValueError("Impossible de récupérer l'email depuis le provider OAuth")
            
            # Rechercher un utilisateur existant
            existing_user = self._find_oauth_user(provider, user_info)
            
            if existing_user:
                # Utilisateur existant - mettre à jour les informations
                existing_user.derniere_connexion = datetime.utcnow()
                
                # Mettre à jour les informations si elles ont changé
                if user_info.get('name') and not existing_user.nom:
                    self._update_user_name_from_oauth(existing_user, user_info.get('name'))
                
                self.db.commit()
                logger.info(f"Connexion OAuth réussie pour l'utilisateur existant: {existing_user.email}")
                
                return existing_user, False
            
            else:
                # Nouvel utilisateur - créer le compte
                new_user = self._create_oauth_user(provider, user_info)
                logger.info(f"Nouveau compte créé via OAuth {provider}: {new_user.email}")
                
                return new_user, True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification OAuth {provider}: {str(e)}")
            raise ValueError(f"Erreur d'authentification OAuth: {str(e)}")
    
    def link_oauth_account(self,
                          user_id: int,
                          provider: str,
                          access_token: str,
                          id_token: Optional[str] = None) -> bool:
        """
        Lier un compte OAuth à un utilisateur existant
        
        Args:
            user_id: ID de l'utilisateur
            provider: Provider OAuth à lier
            access_token: Token d'accès OAuth
            id_token: Token ID optionnel
        
        Returns:
            True si la liaison a réussi
        """
        
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        provider = provider.lower()
        
        if provider not in self.OAUTH_CONFIGS:
            raise ValueError(f"Provider OAuth non supporté: {provider}")
        
        try:
            # Récupérer les informations OAuth
            user_info = self._get_oauth_user_info(provider, access_token, id_token)
            
            # Vérifier si ce compte OAuth n'est pas déjà lié
            existing_oauth = self.db.query(UtilisateurOAuth).filter_by(
                provider=provider,
                provider_user_id=user_info['id']
            ).first()
            
            if existing_oauth:
                if existing_oauth.utilisateur_id == user_id:
                    logger.info(f"Le compte {provider} est déjà lié à cet utilisateur")
                    return True
                else:
                    raise ValueError(f"Ce compte {provider} est déjà lié à un autre utilisateur")
            
            # Créer la liaison OAuth
            oauth_link = UtilisateurOAuth(
                utilisateur_id=user_id,
                provider=provider,
                provider_user_id=user_info['id'],
                provider_email=user_info.get('email'),
                provider_username=user_info.get('username'),
                access_token=access_token,
                refresh_token=user_info.get('refresh_token'),
                token_expires_at=user_info.get('expires_at')
            )
            
            self.db.add(oauth_link)
            self.db.commit()
            
            logger.info(f"Compte {provider} lié avec succès pour l'utilisateur {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la liaison OAuth {provider}: {str(e)}")
            self.db.rollback()
            raise
    
    def unlink_oauth_account(self, user_id: int, provider: str) -> bool:
        """
        Délier un compte OAuth d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            provider: Provider OAuth à délier
        
        Returns:
            True si la suppression a réussi
        """
        
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # Vérifier que l'utilisateur a un mot de passe ou un autre moyen de connexion
        oauth_count = self.db.query(UtilisateurOAuth).filter_by(
            utilisateur_id=user_id
        ).count()
        
        if oauth_count <= 1 and not user.mot_de_passe_hash:
            raise ValueError("Impossible de délier le dernier moyen de connexion. Définissez d'abord un mot de passe.")
        
        # Supprimer la liaison
        oauth_link = self.db.query(UtilisateurOAuth).filter_by(
            utilisateur_id=user_id,
            provider=provider.lower()
        ).first()
        
        if oauth_link:
            self.db.delete(oauth_link)
            self.db.commit()
            logger.info(f"Compte {provider} délié pour l'utilisateur {user_id}")
            return True
        
        return False
    
    def get_oauth_accounts(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtenir la liste des comptes OAuth liés
        
        Returns:
            Liste des providers OAuth liés
        """
        
        oauth_accounts = self.db.query(UtilisateurOAuth).filter_by(
            utilisateur_id=user_id
        ).all()
        
        return [
            {
                'provider': account.provider,
                'provider_email': account.provider_email,
                'provider_username': account.provider_username,
                'linked_at': account.cree_le
            }
            for account in oauth_accounts
        ]
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Changer le mot de passe d'un utilisateur"""
        
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # Vérifier l'ancien mot de passe si l'utilisateur en a un
        if user.mot_de_passe_hash:
            if not bcrypt.checkpw(old_password.encode('utf-8'), 
                                user.mot_de_passe_hash.encode('utf-8')):
                raise ValueError("Mot de passe actuel incorrect")
        
        # Valider le nouveau mot de passe
        if not self._validate_password(new_password):
            raise ValueError("Le nouveau mot de passe doit contenir au moins 8 caractères")
        
        # Hasher et enregistrer le nouveau mot de passe
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.mot_de_passe_hash = password_hash.decode('utf-8')
        user.modifie_le = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def verify_email(self, token: str) -> bool:
        """Vérifier l'email avec le token"""
        user = self.db.query(Utilisateur).filter_by(
            token_verification_email=token
        ).first()
        
        if user:
            user.email_verifie = True
            user.email_verifie_le = datetime.utcnow()
            user.token_verification_email = None
            self.db.commit()
            return True
        
        return False
    
    def request_password_reset(self, email: str) -> Optional[str]:
        """Demander une réinitialisation de mot de passe"""
        user = self.get_by_email(email)
        
        if user:
            token = self._generate_token()
            user.token_reset_password = token
            user.token_reset_expire_le = datetime.utcnow() + timedelta(hours=24)
            self.db.commit()
            return token
        
        return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Réinitialiser le mot de passe"""
        user = self.db.query(Utilisateur).filter_by(
            token_reset_password=token
        ).first()
        
        if not user:
            return False
        
        if user.token_reset_expire_le < datetime.utcnow():
            return False
        
        if not self._validate_password(new_password):
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.mot_de_passe_hash = password_hash.decode('utf-8')
        user.token_reset_password = None
        user.token_reset_expire_le = None
        self.db.commit()
        
        return True
    
    def update_profile(self,
                      user_id: int,
                      nom_utilisateur: Optional[str] = None,
                      email: Optional[str] = None,
                      prenom: Optional[str] = None,
                      nom: Optional[str] = None) -> Utilisateur:
        """Mettre à jour le profil utilisateur"""
        
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # Valider et mettre à jour le nom d'utilisateur
        if nom_utilisateur and nom_utilisateur != user.nom_utilisateur:
            if not self._validate_username(nom_utilisateur):
                raise ValueError("Nom d'utilisateur invalide")
            
            if self.get_by_username(nom_utilisateur):
                raise ValueError("Ce nom d'utilisateur est déjà pris")
            
            user.nom_utilisateur = nom_utilisateur
        
        # Valider et mettre à jour l'email
        if email and email != user.email:
            if not self._validate_email(email):
                raise ValueError("Format d'email invalide")
            
            if self.get_by_email(email):
                raise ValueError("Cet email est déjà utilisé")
            
            user.email = email
            user.email_verifie = False  # Nécessite une nouvelle vérification
            user.token_verification_email = self._generate_token()
        
        # Mettre à jour les autres champs
        if prenom is not None:
            user.prenom = prenom
        
        if nom is not None:
            user.nom = nom
        
        user.modifie_le = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def update_preferences(self, 
                          user_id: int,
                          mode_sombre: Optional[bool] = None,
                          taille_police: Optional[str] = None,
                          langue: Optional[str] = None,
                          timezone: Optional[str] = None) -> Utilisateur:
        """Mettre à jour les préférences utilisateur"""
        
        user = self.get_by_id(user_id)
        
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        if mode_sombre is not None:
            user.mode_sombre = mode_sombre
        
        if taille_police is not None:
            if taille_police not in ['small', 'medium', 'large', 'x-large']:
                raise ValueError("Taille de police invalide")
            user.taille_police = taille_police
        
        if langue is not None:
            if langue not in ['fr', 'en', 'es', 'de', 'it']:
                raise ValueError("Langue non supportée")
            user.langue = langue
        
        if timezone is not None:
            # TODO: Valider le timezone
            user.timezone = timezone
        
        user.modifie_le = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtenir les statistiques détaillées de l'utilisateur"""
        
        stats = {
            'total_articles_lus': 0,
            'total_favoris': 0,
            'total_flux': 0,
            'total_collections': 0,
            'total_collections_partagees': 0,
            'total_commentaires': 0,
            'articles_lus_cette_semaine': 0,
            'articles_lus_ce_mois': 0
        }
        
        # Articles lus et favoris
        statuts = self.db.query(StatutUtilisateurArticle).filter_by(
            utilisateur_id=user_id
        ).all()
        
        stats['total_articles_lus'] = sum(1 for s in statuts if s.est_lu)
        stats['total_favoris'] = sum(1 for s in statuts if s.est_favori)
        
        # Articles lus récemment
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        stats['articles_lus_cette_semaine'] = sum(
            1 for s in statuts 
            if s.est_lu and s.lu_le and s.lu_le >= week_ago
        )
        
        stats['articles_lus_ce_mois'] = sum(
            1 for s in statuts 
            if s.est_lu and s.lu_le and s.lu_le >= month_ago
        )
        
        # Collections
        stats['total_collections'] = self.db.query(Collection).filter_by(
            proprietaire_id=user_id
        ).count()
        
        # Collections partagées (où l'utilisateur est membre)
        stats['total_collections_partagees'] = self.db.query(MembreCollection).filter(
            MembreCollection.utilisateur_id == user_id,
            MembreCollection.collection_id.in_(
                self.db.query(Collection.id).filter(Collection.est_partagee == True)
            )
        ).count()
        
        # Flux via catégories
        categories = self.db.query(Categorie).filter_by(
            utilisateur_id=user_id
        ).all()
        
        flux_ids = set()
        for cat in categories:
            for fc in cat.flux_categorie:
                flux_ids.add(fc.flux_id)
        
        stats['total_flux'] = len(flux_ids)
        
        # Commentaires
        stats['total_commentaires'] = self.db.query(CommentaireArticle).filter_by(
            utilisateur_id=user_id
        ).count()
        
        return stats
    
    def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Rechercher des utilisateurs par nom d'utilisateur ou email
        (pour inviter dans des collections)
        """
        
        search_pattern = f'%{query}%'
        
        users = self.db.query(Utilisateur).filter(
            Utilisateur.est_actif == True,
            or_(
                Utilisateur.nom_utilisateur.ilike(search_pattern),
                Utilisateur.email.ilike(search_pattern),
                Utilisateur.prenom.ilike(search_pattern),
                Utilisateur.nom.ilike(search_pattern)
            )
        ).limit(limit).all()
        
        return [
            {
                'id': user.id,
                'nom_utilisateur': user.nom_utilisateur,
                'email': user.email,
                'nom_complet': f"{user.prenom or ''} {user.nom or ''}".strip() or user.nom_utilisateur
            }
            for user in users
        ]
    
    def get_by_id(self, user_id: int) -> Optional[Utilisateur]:
        """Obtenir un utilisateur par ID"""
        return self.db.query(Utilisateur).filter_by(id=user_id).first()
    
    def get_by_email(self, email: str) -> Optional[Utilisateur]:
        """Obtenir un utilisateur par email"""
        return self.db.query(Utilisateur).filter_by(email=email).first()
    
    def get_by_username(self, username: str) -> Optional[Utilisateur]:
        """Obtenir un utilisateur par nom d'utilisateur"""
        return self.db.query(Utilisateur).filter_by(nom_utilisateur=username).first()
    
    def delete_user(self, user_id: int) -> bool:
        """Supprimer un utilisateur (soft delete)"""
        user = self.get_by_id(user_id)
        
        if user:
            user.est_actif = False
            user.modifie_le = datetime.utcnow()
            
            # Anonymiser les données personnelles (RGPD)
            user.email = f"deleted_{user.id}@deleted.com"
            user.nom_utilisateur = f"deleted_user_{user.id}"
            user.prenom = None
            user.nom = None
            user.mot_de_passe_hash = None
            
            self.db.commit()
            logger.info(f"Utilisateur {user_id} supprimé (soft delete)")
            return True
        
        return False
    
    # ==================== MÉTHODES PRIVÉES ====================
    
    def _get_oauth_user_info(self, provider: str, access_token: str, id_token: Optional[str]) -> Dict[str, Any]:
        """Récupérer les informations utilisateur depuis le provider OAuth"""
        
        config = self.OAUTH_CONFIGS[provider]
        
        if provider == 'google':
            return self._get_google_user_info(access_token, id_token)
        elif provider == 'microsoft':
            return self._get_microsoft_user_info(access_token, id_token)
        elif provider == 'github':
            return self._get_github_user_info(access_token)
        else:
            raise ValueError(f"Provider non supporté: {provider}")
    
    def _get_google_user_info(self, access_token: str, id_token: Optional[str]) -> Dict[str, Any]:
        """Récupérer les infos utilisateur Google"""
        
        # Si on a un ID token, on peut le valider
        if id_token:
            try:
                # Valider le token avec les clés publiques de Google
                jwks_client = PyJWKClient(self.OAUTH_CONFIGS['google']['jwks_url'])
                signing_key = jwks_client.get_signing_key_from_jwt(id_token)
                
                decoded = jwt.decode(
                    id_token,
                    signing_key.key,
                    algorithms=["RS256"],
                    issuer=self.OAUTH_CONFIGS['google']['issuer']
                )
                
                return {
                    'id': decoded.get('sub'),
                    'email': decoded.get('email'),
                    'email_verified': decoded.get('email_verified', False),
                    'name': decoded.get('name'),
                    'given_name': decoded.get('given_name'),
                    'family_name': decoded.get('family_name'),
                    'picture': decoded.get('picture')
                }
            except Exception as e:
                logger.error(f"Erreur validation ID token Google: {e}")
        
        # Sinon, utiliser l'API userinfo
        with httpx.Client() as client:
            response = client.get(
                self.OAUTH_CONFIGS['google']['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Erreur lors de la récupération des infos Google: {response.text}")
            
            data = response.json()
            
            return {
                'id': data.get('sub'),
                'email': data.get('email'),
                'email_verified': data.get('email_verified', False),
                'name': data.get('name'),
                'given_name': data.get('given_name'),
                'family_name': data.get('family_name'),
                'picture': data.get('picture')
            }
    
    def _get_microsoft_user_info(self, access_token: str, id_token: Optional[str]) -> Dict[str, Any]:
        """Récupérer les infos utilisateur Microsoft"""
        
        with httpx.Client() as client:
            response = client.get(
                self.OAUTH_CONFIGS['microsoft']['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Erreur lors de la récupération des infos Microsoft: {response.text}")
            
            data = response.json()
            
            return {
                'id': data.get('id'),
                'email': data.get('mail') or data.get('userPrincipalName'),
                'name': data.get('displayName'),
                'given_name': data.get('givenName'),
                'family_name': data.get('surname'),
                'username': data.get('userPrincipalName')
            }
    
    def _get_github_user_info(self, access_token: str) -> Dict[str, Any]:
        """Récupérer les infos utilisateur GitHub"""
        
        with httpx.Client() as client:
            # Récupérer les infos de base
            response = client.get(
                self.OAUTH_CONFIGS['github']['userinfo_url'],
                headers={'Authorization': f'token {access_token}'}
            )
            
            if response.status_code != 200:
                raise ValueError(f"Erreur lors de la récupération des infos GitHub: {response.text}")
            
            data = response.json()
            
            # GitHub ne fournit pas toujours l'email dans l'API user
            email = data.get('email')
            
            if not email:
                # Récupérer l'email depuis l'API emails
                email_response = client.get(
                    self.OAUTH_CONFIGS['github']['email_url'],
                    headers={'Authorization': f'token {access_token}'}
                )
                
                if email_response.status_code == 200:
                    emails = email_response.json()
                    # Chercher l'email principal et vérifié
                    for e in emails:
                        if e.get('primary') and e.get('verified'):
                            email = e.get('email')
                            break
            
            return {
                'id': str(data.get('id')),
                'email': email,
                'name': data.get('name'),
                'username': data.get('login'),
                'avatar_url': data.get('avatar_url')
            }
    
    def _find_oauth_user(self, provider: str, user_info: Dict[str, Any]) -> Optional[Utilisateur]:
        """Rechercher un utilisateur existant via OAuth"""
        
        # Chercher par liaison OAuth existante
        oauth_link = self.db.query(UtilisateurOAuth).filter_by(
            provider=provider,
            provider_user_id=user_info['id']
        ).first()
        
        if oauth_link:
            return oauth_link.utilisateur
        
        # Chercher par email (si l'utilisateur existe déjà)
        email = user_info.get('email')
        if email:
            user = self.get_by_email(email)
            if user:
                # Créer automatiquement la liaison OAuth
                oauth_link = UtilisateurOAuth(
                    utilisateur_id=user.id,
                    provider=provider,
                    provider_user_id=user_info['id'],
                    provider_email=email,
                    provider_username=user_info.get('username')
                )
                self.db.add(oauth_link)
                self.db.commit()
                
                return user
        
        return None
    
    def _create_oauth_user(self, provider: str, user_info: Dict[str, Any]) -> Utilisateur:
        """Créer un nouvel utilisateur depuis OAuth"""
        
        # Générer un nom d'utilisateur unique
        base_username = (
            user_info.get('username') or 
            user_info.get('email', '').split('@')[0] or
            f"{provider}_user"
        )
        
        username = self._generate_unique_username(base_username)
        
        # Extraire prénom et nom
        prenom = user_info.get('given_name')
        nom = user_info.get('family_name')
        
        # Si on n'a que le nom complet
        if not prenom and not nom and user_info.get('name'):
            parts = user_info.get('name').split(' ', 1)
            prenom = parts[0] if parts else None
            nom = parts[1] if len(parts) > 1 else None
        
        # Créer l'utilisateur
        user = self.create_user(
            nom_utilisateur=username,
            email=user_info['email'],
            mot_de_passe=None,
            prenom=prenom,
            nom=nom,
            is_oauth=True
        )
        
        # Créer la liaison OAuth
        oauth_link = UtilisateurOAuth(
            utilisateur_id=user.id,
            provider=provider,
            provider_user_id=user_info['id'],
            provider_email=user_info.get('email'),
            provider_username=user_info.get('username')
        )
        
        self.db.add(oauth_link)
        self.db.commit()
        
        return user
    
    def _generate_unique_username(self, base_username: str) -> str:
        """Générer un nom d'utilisateur unique"""
        
        # Nettoyer le nom d'utilisateur de base
        clean_username = re.sub(r'[^a-zA-Z0-9_-]', '', base_username)[:45]
        
        if not clean_username:
            clean_username = 'user'
        
        # Vérifier l'unicité
        username = clean_username
        counter = 1
        
        while self.get_by_username(username):
            username = f"{clean_username}_{counter}"
            counter += 1
        
        return username
    
    def _update_user_name_from_oauth(self, user: Utilisateur, name: str):
        """Mettre à jour le nom de l'utilisateur depuis OAuth"""
        
        if name:
            parts = name.split(' ', 1)
            if not user.prenom and parts:
                user.prenom = parts[0]
            if not user.nom and len(parts) > 1:
                user.nom = parts[1]
    
    def _validate_email(self, email: str) -> bool:
        """Valider le format de l'email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> bool:
        """Valider la force du mot de passe"""
        # Au minimum 8 caractères
        if len(password) < 8:
            return False
        
        # Optionnel : ajouter d'autres critères
        # has_upper = any(c.isupper() for c in password)
        # has_lower = any(c.islower() for c in password)
        # has_digit = any(c.isdigit() for c in password)
        
        return True
    
    def _validate_username(self, username: str) -> bool:
        """Valider le nom d'utilisateur"""
        if not 3 <= len(username) <= 50:
            return False
        return re.match(r'^[a-zA-Z0-9_-]+$', username) is not None
    
    def _generate_token(self) -> str:
        """Générer un token sécurisé"""
        return secrets.token_urlsafe(32)
    
    def _create_default_category(self, user_id: int):
        """Créer une catégorie par défaut pour l'utilisateur"""
        default_category = Categorie(
            nom="Non classé",
            utilisateur_id=user_id,
            couleur="#808080"
        )
        self.db.add(default_category)
        self.db.commit()
    
    def _create_default_collection(self, user_id: int):
        """Créer une collection personnelle par défaut"""
        from .collection_business import CollectionBusiness
        
        collection_business = CollectionBusiness(self.db)
        collection_business.create_collection(
            proprietaire_id=user_id,
            nom="Ma collection personnelle",
            description="Collection personnelle pour organiser mes flux RSS",
            est_partagee=False
        )