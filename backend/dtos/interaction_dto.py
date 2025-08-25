# dtos/interaction_dto.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CommentCreateDTO(BaseModel):
    """DTO pour créer un commentaire"""
    article_id: int
    collection_id: int
    contenu: str = Field(..., min_length=1, max_length=5000)
    commentaire_parent_id: Optional[int] = None

class CommentUpdateDTO(BaseModel):
    """DTO pour modifier un commentaire"""
    contenu: str = Field(..., min_length=1, max_length=5000)

class CommentResponseDTO(BaseModel):
    """DTO pour la réponse d'un commentaire"""
    id: int
    article_id: int
    utilisateur_id: int
    utilisateur_nom: str
    collection_id: int
    contenu: str
    commentaire_parent_id: Optional[int] = None
    est_modifie: bool = False
    cree_le: datetime
    modifie_le: Optional[datetime] = None
    reponses: Optional[List['CommentResponseDTO']] = []
    
    class Config:
        orm_mode = True

# Mise à jour des références circulaires
CommentResponseDTO.update_forward_refs()

class MessageCreateDTO(BaseModel):
    """DTO pour envoyer un message"""
    collection_id: int
    contenu: str = Field(..., min_length=1, max_length=2000)

class MessageResponseDTO(BaseModel):
    """DTO pour la réponse d'un message"""
    id: int
    collection_id: int
    utilisateur_id: int
    utilisateur_nom: str
    contenu: str
    est_modifie: bool = False
    cree_le: datetime
    modifie_le: Optional[datetime] = None
    
    class Config:
        orm_mode = True
