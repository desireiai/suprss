# dto/collection_dto.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
from pydantic.networks import EmailStr
from .rss_dto import FluxResponseDTO, MemberRoleEnum
from pydantic import validator
class CollectionCreateDTO(BaseModel):
    """DTO pour créer une collection"""
    nom: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    est_partagee: bool = False

class CollectionUpdateDTO(BaseModel):
    """DTO pour mettre à jour une collection"""
    nom: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class CollectionFluxAddDTO(BaseModel):
    """DTO pour ajouter un flux à une collection"""
    flux_id: int

class MemberRoleEnum(str, Enum):
    PROPRIETAIRE = "proprietaire"
    ADMINISTRATEUR = "administrateur"
    MODERATEUR = "moderateur"
    MEMBRE = "membre"

class CollectionMemberAddDTO(BaseModel):
    """DTO pour ajouter un membre à une collection"""
    utilisateur_id: Optional[int] = None
    email: Optional[EmailStr] = None  # Alternative: inviter par email
    role: MemberRoleEnum = MemberRoleEnum.MEMBRE
    permissions_custom: Optional[Dict[str, bool]] = None
    
    @validator('permissions_custom')
    def validate_permissions(cls, v):
        if v:
            valid_keys = {'peut_ajouter_flux', 'peut_lire', 'peut_commenter', 'peut_modifier', 'peut_supprimer'}
            if not all(k in valid_keys for k in v.keys()):
                raise ValueError('Permissions invalides')
        return v

class CollectionMemberUpdateDTO(BaseModel):
    """DTO pour mettre à jour un membre"""
    role: Optional[MemberRoleEnum] = None
    peut_ajouter_flux: Optional[bool] = None
    peut_lire: Optional[bool] = None
    peut_commenter: Optional[bool] = None
    peut_modifier: Optional[bool] = None
    peut_supprimer: Optional[bool] = None

class CollectionMemberResponseDTO(BaseModel):
    """DTO pour la réponse d'un membre"""
    id: int
    nom_utilisateur: str
    email: str
    role: str
    rejoint_le: datetime
    permissions: Dict[str, bool]
    
    class Config:
        orm_mode = True

class CollectionResponseDTO(BaseModel):
    """DTO pour la réponse d'une collection"""
    id: int
    nom: str
    description: Optional[str]
    est_partagee: bool
    proprietaire_id: int
    proprietaire_nom: str
    nombre_flux: int
    nombre_membres: int
    mon_role: Optional[str]
    mes_permissions: Optional[Dict[str, bool]]
    cree_le: datetime
    modifie_le: Optional[datetime]
    
    class Config:
        orm_mode = True

class CollectionDetailResponseDTO(CollectionResponseDTO):
    """DTO détaillé pour une collection"""
    flux: List[FluxResponseDTO]
    membres: List[CollectionMemberResponseDTO]