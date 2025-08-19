# dto/import_export_dto.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime
from enum import Enum

class ExportFormatEnum(str, Enum):
    OPML = "opml"
    JSON = "json"
    CSV = "csv"

class ExportRequestDTO(BaseModel):
    """DTO pour demander un export"""
    format: ExportFormatEnum
    include_collections: bool = True
    include_personal_flux: bool = True
    include_categories: bool = True
    include_read_status: bool = False
    include_favorites: bool = False

class ImportFileDTO(BaseModel):
    """DTO pour importer un fichier"""
    format: ExportFormatEnum
    content: str  # Contenu du fichier en base64 ou texte
    merge_strategy: Literal["skip", "replace", "merge"] = "merge"
    default_category_id: Optional[int] = None

class OpmlOutlineDTO(BaseModel):
    """DTO pour un élément OPML"""
    text: str
    title: Optional[str]
    type: Optional[str]
    xmlUrl: Optional[str]
    htmlUrl: Optional[str]
    category: Optional[str]

class ImportResultDTO(BaseModel):
    """DTO pour le résultat d'import"""
    success: bool
    imported_flux: int
    skipped_flux: int
    errors: List[str]
    created_categories: List[str]
    details: Dict[str, Any]