# dto/rss_dto.py
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Literal
from datetime import datetime

class FluxCreateDTO(BaseModel):
    """DTO pour créer un flux RSS"""
    url: HttpUrl
    nom_personnalise: Optional[str] = Field(None, max_length=255)
    categorie_id: Optional[int] = None
    frequence_maj_heures: int = Field(default=6, ge=1, le=168)  # Entre 1h et 1 semaine

class FluxUpdateDTO(BaseModel):
    """DTO pour mettre à jour un flux"""
    nom: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    frequence_maj_heures: Optional[int] = Field(None, ge=1, le=168)
    est_actif: Optional[bool] = None

class FluxResponseDTO(BaseModel):
    """DTO pour la réponse d'un flux"""
    id: int
    nom: str
    url: str
    description: Optional[str]
    frequence_maj_heures: int
    est_actif: bool
    derniere_maj: Optional[datetime]
    nombre_articles: Optional[int] = 0
    cree_le: datetime
    
    class Config:
        orm_mode = True

class ArticleResponseDTO(BaseModel):
    """DTO pour la réponse d'un article"""
    id: int
    titre: str
    lien: str
    auteur: Optional[str]
    resume: Optional[str]
    contenu: Optional[str]
    publie_le: Optional[datetime]
    flux_id: int
    flux_nom: str
    est_lu: bool = False
    est_favori: bool = False
    
    class Config:
        orm_mode = True

class ArticleStatusUpdateDTO(BaseModel):
    """DTO pour mettre à jour le statut d'un article"""
    est_lu: Optional[bool] = None
    est_favori: Optional[bool] = None

class ArticleFilterDTO(BaseModel):
    """DTO pour filtrer les articles"""
    categorie_id: Optional[int] = None
    flux_id: Optional[int] = None
    only_unread: bool = False
    only_favorites: bool = False
    search_query: Optional[str] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

class ArticleBulkActionDTO(BaseModel):
    """DTO pour les actions en masse sur les articles"""
    article_ids: List[int]
    action: Literal["mark_read", "mark_unread", "add_favorite", "remove_favorite"]