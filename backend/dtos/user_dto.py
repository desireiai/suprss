# dto/user_dto.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaillePolicEnum(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    X_LARGE = "x-large"

class UserRegisterDTO(BaseModel):
    """DTO pour l'inscription d'un utilisateur"""
    nom_utilisateur: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    mot_de_passe: str = Field(..., min_length=8)
    prenom: Optional[str] = Field(None, max_length=100)
    nom: Optional[str] = Field(None, max_length=100)
    
    @validator('mot_de_passe')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Le mot de passe doit contenir au moins 8 caractères')
        return v

class UserLoginDTO(BaseModel):
    """DTO pour la connexion"""
    email: EmailStr
    mot_de_passe: str

class OAuth2LoginDTO(BaseModel):
    """DTO pour la connexion OAuth2"""
    provider: str = Field(..., regex="^(google|microsoft|github)$")
    token: str
    email: Optional[EmailStr] = None

class UserUpdateDTO(BaseModel):
    """DTO pour la mise à jour du profil"""
    nom_utilisateur: Optional[str] = Field(None, min_length=3, max_length=50)
    prenom: Optional[str] = Field(None, max_length=100)
    nom: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None

class UserPreferencesDTO(BaseModel):
    """DTO pour les préférences utilisateur"""
    mode_sombre: Optional[bool] = None
    taille_police: Optional[TaillePolicEnum] = None

class PasswordChangeDTO(BaseModel):
    """DTO pour le changement de mot de passe"""
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str = Field(..., min_length=8)

class PasswordResetRequestDTO(BaseModel):
    """DTO pour la demande de réinitialisation"""
    email: EmailStr

class PasswordResetDTO(BaseModel):
    """DTO pour la réinitialisation du mot de passe"""
    token: str
    nouveau_mot_de_passe: str = Field(..., min_length=8)

class UserResponseDTO(BaseModel):
    """DTO pour la réponse utilisateur"""
    id: int
    nom_utilisateur: str
    email: str
    prenom: Optional[str]
    nom: Optional[str]
    est_actif: bool
    email_verifie: bool
    mode_sombre: bool
    taille_police: str
    derniere_connexion: Optional[datetime]
    cree_le: datetime
    
    class Config:
        orm_mode = True

class UserStatsDTO(BaseModel):
    """DTO pour les statistiques utilisateur"""
    total_articles_lus: int
    total_favoris: int
    total_flux: int
    total_collections: int
    total_commentaires: int

class TokenResponseDTO(BaseModel):
    """DTO pour la réponse d'authentification"""
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponseDTO