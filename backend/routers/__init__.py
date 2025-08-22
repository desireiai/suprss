# routers/__init__.py
"""Module routers contenant les endpoints de l'API"""

# Import conditionnel des routers pour éviter les erreurs
try:
    from .user_router import router as user_router
except ImportError:
    user_router = None

try:
    from .rss_router import router as rss_router
except ImportError:
    rss_router = None

try:
    from .category_router import router as category_router
except ImportError:
    category_router = None

try:
    from .collection_router import router as collection_router
except ImportError:
    collection_router = None

try:
    from .interaction_router import router as interaction_router
except ImportError:
    interaction_router = None

try:
    from .search_router import router as search_router
except ImportError:
    search_router = None

__all__ = [
    "user_router",
    "rss_router", 
    "category_router",
    "collection_router",
    "interaction_router",
    "search_router"
]