# core/security.py
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging

from core.config import settings

logger = logging.getLogger(__name__)

# Configuration du contexte de hachage de mot de passe
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS
)

def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT d'accès"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Crée un token JWT de rafraîchissement"""
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def verify_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
    """Vérifie et décode un token JWT"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Vérifier le type de token
        token_type = payload.get("type")
        expected_type = "refresh" if is_refresh else "access"
        
        if token_type != expected_type:
            raise jwt.InvalidTokenError(f"Token type invalide. Attendu: {expected_type}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Token invalide: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

def generate_email_verification_token(email: str, user_id: int) -> str:
    """Génère un token pour la vérification d'email"""
    data = {
        "email": email,
        "user_id": user_id,
        "purpose": "email_verification"
    }
    
    expire = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    data["exp"] = expire
    
    token = jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return token

def verify_email_verification_token(token: str) -> Optional[Dict[str, Any]]:
    """Vérifie un token de vérification d'email"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("purpose") != "email_verification":
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token de vérification d'email expiré")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Token de vérification d'email invalide")
        return None

def generate_password_reset_token(email: str, user_id: int) -> str:
    """Génère un token pour la réinitialisation de mot de passe"""
    data = {
        "email": email,
        "user_id": user_id,
        "purpose": "password_reset",
        "random": secrets.token_urlsafe(16)  # Ajouter de l'aléatoire
    }
    
    expire = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    data["exp"] = expire
    
    token = jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return token

def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """Vérifie un token de réinitialisation de mot de passe"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("purpose") != "password_reset":
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token de réinitialisation expiré")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Token de réinitialisation invalide")
        return None

def generate_secure_token(length: int = 32) -> str:
    """Génère un token sécurisé aléatoire"""
    return secrets.token_urlsafe(length)

def generate_api_key() -> str:
    """Génère une clé API unique"""
    prefix = "sk_"  # Secret Key prefix
    key = secrets.token_urlsafe(32)
    return f"{prefix}{key}"

def hash_api_key(api_key: str) -> str:
    """Hache une clé API pour le stockage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force d'un mot de passe.
    Retourne (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    if not any(c.islower() for c in password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial"
    
    # Vérifier les mots de passe communs
    common_passwords = [
        "password", "123456", "password123", "admin", "letmein",
        "qwerty", "abc123", "monkey", "master", "dragon"
    ]
    if password.lower() in common_passwords:
        return False, "Ce mot de passe est trop commun"
    
    return True, ""

def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """
    Nettoie une chaîne d'entrée pour éviter les injections.
    """
    if not input_string:
        return ""
    
    # Limiter la longueur
    input_string = input_string[:max_length]
    
    # Supprimer les caractères de contrôle
    import unicodedata
    cleaned = "".join(
        char for char in input_string 
        if unicodedata.category(char)[0] != "C"
    )
    
    return cleaned.strip()

def generate_csrf_token() -> str:
    """Génère un token CSRF"""
    return secrets.token_urlsafe(32)

def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Vérifie un token CSRF"""
    return secrets.compare_digest(token, stored_token)

class RateLimiter:
    """Gestionnaire de limitation de taux"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Vérifie si la limite de taux est atteinte.
        Retourne (is_allowed, info)
        """
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - window
        
        # Nettoyer les anciennes entrées
        await self.redis.zremrangebyscore(key, 0, window_start)
        
        # Compter les requêtes dans la fenêtre
        request_count = await self.redis.zcard(key)
        
        if request_count >= limit:
            # Limite atteinte
            retry_after = await self.redis.zrange(key, 0, 0, withscores=True)
            if retry_after:
                retry_time = int(retry_after[0][1]) + window - current_time
            else:
                retry_time = window
            
            return False, {
                "limit": limit,
                "remaining": 0,
                "reset": current_time + retry_time
            }
        
        # Ajouter la nouvelle requête
        await self.redis.zadd(key, {str(current_time): current_time})
        await self.redis.expire(key, window)
        
        return True, {
            "limit": limit,
            "remaining": limit - request_count - 1,
            "reset": current_time + window
        }

def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """
    Chiffre des données sensibles.
    Utilise Fernet pour le chiffrement symétrique.
    """
    from cryptography.fernet import Fernet
    
    if not key:
        key = settings.SECRET_KEY[:32].encode()
        key = hashlib.sha256(key).digest()
        key = base64.urlsafe_b64encode(key)
    
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    
    return encrypted.decode()

def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """Déchiffre des données sensibles"""
    from cryptography.fernet import Fernet
    import base64
    
    if not key:
        key = settings.SECRET_KEY[:32].encode()
        key = hashlib.sha256(key).digest()
        key = base64.urlsafe_b64encode(key)
    
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data.encode())
    
    return decrypted.decode()