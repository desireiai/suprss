# routers/__init__.py
"""Module routers contenant les endpoints de l'API"""

from .user_router import router as user_router
from .rss_router import router as rss_router
from .category_router import router as category_router
from .collection_router import router as collection_router
from .interaction_router import router as interaction_router
from .search_router import router as search_router

__all__ = [
    "user_router",
    "rss_router",
    "category_router",
    "collection_router",
    "interaction_router",
    "search_router"
]
