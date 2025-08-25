# dtos/search_dto.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any

class GlobalSearchDTO(BaseModel):
    """DTO pour la recherche globale"""
    query: str = Field(..., min_length=2, max_length=200)
    search_in: List[Literal["articles", "flux", "collections", "comments"]] = ["articles"]
    limit_per_type: int = Field(default=10, ge=1, le=50)

class SearchResultDTO(BaseModel):
    """DTO pour les résultats de recherche"""
    type: str
    id: int
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    match_snippet: Optional[str] = None
    relevance_score: float = 0.0  # Toujours fourni par le business
    metadata: Dict[str, Any] = {}