# dto/pagination_dto.py
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional, Literal

T = TypeVar('T')

class PaginationParamsDTO(BaseModel):
    """DTO pour les paramètres de pagination"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "desc"

class PaginatedResponseDTO(BaseModel, Generic[T]):
    """DTO générique pour les réponses paginées"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    class Config:
        arbitrary_types_allowed = True