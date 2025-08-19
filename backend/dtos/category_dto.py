# dto/category_dto.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re

class CategoryCreateDTO(BaseModel):
    """DTO pour créer une catégorie"""
    nom: str = Field(..., min_length=1, max_length=100)
    couleur: str = Field(default="#007bff", regex="^#[0-9A-Fa-f]{6}$")
    
    @validator('couleur')
    def validate_color(cls, v):
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Format de couleur invalide (utilisez #RRGGBB)')
        return v

class CategoryUpdateDTO(BaseModel):
    """DTO pour mettre à jour une catégorie"""
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    couleur: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")

class CategoryResponseDTO(BaseModel):
    """DTO pour la réponse d'une catégorie"""
    id: int
    nom: str
    couleur: str
    nombre_flux: int
    cree_le: datetime
    
    class Config:
        orm_mode = True

class CategoryFluxMoveDTO(BaseModel):
    """DTO pour déplacer un flux entre catégories"""
    flux_id: int
    from_category_id: int
    to_category_id: int
