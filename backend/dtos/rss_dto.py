# dtos/rss_dto.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Literal, Generic, TypeVar
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
    description: Optional[str] = None
    frequence_maj_heures: int
    est_actif: bool
    derniere_maj: Optional[datetime] = None
    nombre_articles: Optional[int] = 0
    cree_le: datetime
    
    model_config = {"from_attributes": True}

class ArticleResponseDTO(BaseModel):
    """DTO pour la réponse d'un article"""
    id: int
    titre: str
    lien: str
    auteur: Optional[str] = None
    resume: Optional[str] = None
    contenu: Optional[str] = None
    publie_le: Optional[datetime] = None
    flux_id: int
    flux_nom: str
    est_lu: bool = False
    est_favori: bool = False
    
    model_config = {"from_attributes": True}

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

# DTOs de pagination manquants utilisés dans le router
class PaginationParamsDTO(BaseModel):
    """DTO pour les paramètres de pagination"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    sort_by: Optional[str] = Field(default="date")
    sort_order: Literal["asc", "desc"] = Field(default="desc")

# Generic type pour les réponses paginées
T = TypeVar('T')

class PaginatedResponseDTO(BaseModel, Generic[T]):
    """DTO pour les réponses paginées"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

# DTO pour la réponse d'import OPML
class OPMLImportResponseDTO(BaseModel):
    """DTO pour la réponse d'import OPML"""
    message: str
    imported_count: int

# DTO pour les statistiques de flux
class FluxStatsDTO(BaseModel):
    """DTO pour les statistiques d'un flux"""
    total_articles: int
    articles_non_lus: int
    articles_favoris: int
    derniere_publication: Optional[datetime] = None
    moyenne_articles_par_jour: Optional[float] = None