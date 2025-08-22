# routers/search_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from dto.search_dto import (
    GlobalSearchDTO,
    SearchResultDTO
)
from business_models.search_business import SearchBusiness
from routers.user_router import get_current_user
from core.database import get_db

router = APIRouter(prefix="/api/search", tags=["Recherche"])

@router.post("/global", response_model=Dict[str, List[SearchResultDTO]])
async def global_search(
    search_data: GlobalSearchDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Effectue une recherche globale dans l'application.
    Retourne les résultats groupés par type (articles, flux, collections, commentaires).
    """
    search_business = SearchBusiness(db)
    
    # Valider la requête de recherche
    if len(search_data.query.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La requête de recherche doit contenir au moins 2 caractères"
        )
    
    results = {}
    
    # Rechercher dans les articles
    if "articles" in search_data.search_in:
        articles = search_business.search_articles(
            user_id=current_user.id,
            query=search_data.query,
            limit=search_data.limit_per_type
        )
        results["articles"] = articles
    
    # Rechercher dans les flux
    if "flux" in search_data.search_in:
        flux = search_business.search_flux(
            user_id=current_user.id,
            query=search_data.query,
            limit=search_data.limit_per_type
        )
        results["flux"] = flux
    
    # Rechercher dans les collections
    if "collections" in search_data.search_in:
        collections = search_business.search_collections(
            user_id=current_user.id,
            query=search_data.query,
            limit=search_data.limit_per_type
        )
        results["collections"] = collections
    
    # Rechercher dans les commentaires
    if "comments" in search_data.search_in:
        comments = search_business.search_comments(
            user_id=current_user.id,
            query=search_data.query,
            limit=search_data.limit_per_type
        )
        results["comments"] = comments
    
    return results

@router.get("/articles", response_model=List[SearchResultDTO])
async def search_articles(
    q: str = Query(..., min_length=2, max_length=200),
    category_id: Optional[int] = None,
    flux_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    only_unread: bool = False,
    only_favorites: bool = False,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recherche avancée dans les articles avec filtres"""
    search_business = SearchBusiness(db)
    
    results = search_business.search_articles_advanced(
        user_id=current_user.id,
        query=q,
        category_id=category_id,
        flux_id=flux_id,
        date_from=date_from,
        date_to=date_to,
        only_unread=only_unread,
        only_favorites=only_favorites,
        limit=limit,
        offset=offset
    )
    
    return results

@router.get("/flux", response_model=List[SearchResultDTO])
async def search_flux(
    q: str = Query(..., min_length=2, max_length=200),
    category_id: Optional[int] = None,
    only_active: bool = True,
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recherche dans les flux RSS"""
    search_business = SearchBusiness(db)
    
    results = search_business.search_flux_advanced(
        user_id=current_user.id,
        query=q,
        category_id=category_id,
        only_active=only_active,
        limit=limit
    )
    
    return results

@router.get("/collections", response_model=List[SearchResultDTO])
async def search_collections(
    q: str = Query(..., min_length=2, max_length=200),
    only_owned: bool = False,
    include_shared: bool = True,
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Recherche dans les collections"""
    search_business = SearchBusiness(db)
    
    results = search_business.search_collections_advanced(
        user_id=current_user.id,
        query=q,
        only_owned=only_owned,
        include_shared=include_shared,
        limit=limit
    )
    
    return results

@router.get("/suggestions", response_model=List[str])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=50),
    type: str = Query("all", regex="^(all|articles|flux|collections)$"),
    limit: int = Query(10, ge=1, le=20),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère des suggestions de recherche basées sur l'historique
    et les termes populaires
    """
    search_business = SearchBusiness(db)
    
    suggestions = search_business.get_search_suggestions(
        user_id=current_user.id,
        query_prefix=q,
        search_type=type,
        limit=limit
    )
    
    return suggestions

@router.get("/recent", response_model=List[str])
async def get_recent_searches(
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les recherches récentes de l'utilisateur"""
    search_business = SearchBusiness(db)
    
    recent_searches = search_business.get_user_recent_searches(
        user_id=current_user.id,
        limit=limit
    )
    
    return recent_searches

@router.delete("/recent", status_code=status.HTTP_204_NO_CONTENT)
async def clear_recent_searches(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Efface l'historique de recherche de l'utilisateur"""
    search_business = SearchBusiness(db)
    
    search_business.clear_user_search_history(current_user.id)
    
    return None

@router.get("/trending", response_model=List[Dict[str, Any]])
async def get_trending_searches(
    period: str = Query("week", regex="^(day|week|month)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les recherches tendance pour la période donnée.
    Accessible uniquement aux utilisateurs connectés.
    """
    search_business = SearchBusiness(db)
    
    trending = search_business.get_trending_searches(
        period=period,
        limit=limit
    )
    
    return trending

@router.post("/save", status_code=status.HTTP_201_CREATED)
async def save_search(
    query: str = Query(..., min_length=2, max_length=200),
    name: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sauvegarde une recherche pour un accès rapide"""
    search_business = SearchBusiness(db)
    
    saved_search = search_business.save_search(
        user_id=current_user.id,
        query=query,
        name=name or query
    )
    
    return {"message": "Recherche sauvegardée", "id": saved_search.id}

@router.get("/saved", response_model=List[Dict[str, Any]])
async def get_saved_searches(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les recherches sauvegardées de l'utilisateur"""
    search_business = SearchBusiness(db)
    
    saved_searches = search_business.get_user_saved_searches(current_user.id)
    
    return saved_searches

@router.delete("/saved/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime une recherche sauvegardée"""
    search_business = SearchBusiness(db)
    
    # Vérifier que la recherche appartient à l'utilisateur
    if not search_business.user_owns_saved_search(current_user.id, search_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette recherche sauvegardée ne vous appartient pas"
        )
    
    search_business.delete_saved_search(search_id)
    
    return None

@router.get("/stats", response_model=Dict[str, Any])
async def get_search_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les statistiques de recherche de l'utilisateur"""
    search_business = SearchBusiness(db)
    
    stats = search_business.get_user_search_stats(current_user.id)
    
    return stats

@router.post("/index/rebuild", status_code=status.HTTP_202_ACCEPTED)
async def rebuild_search_index(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reconstruit l'index de recherche pour l'utilisateur.
    Cette opération peut prendre du temps et est lancée en arrière-plan.
    """
    search_business = SearchBusiness(db)
    
    # Lancer la reconstruction de l'index en arrière-plan
    from fastapi import BackgroundTasks
    background_tasks = BackgroundTasks()
    background_tasks.add_task(
        search_business.rebuild_user_search_index,
        current_user.id
    )
    
    return {"message": "Reconstruction de l'index lancée"}

@router.get("/filters", response_model=Dict[str, List])
async def get_available_filters(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les filtres disponibles pour la recherche
    (catégories, flux, collections, etc.)
    """
    search_business = SearchBusiness(db)
    from business_models.category_business import CategoryBusiness
    from business_models.rss_business import RSSBusiness
    from business_models.collection_business import CollectionBusiness
    
    category_business = CategoryBusiness(db)
    rss_business = RSSBusiness(db)
    collection_business = CollectionBusiness(db)
    
    # Récupérer toutes les options de filtrage
    categories = category_business.get_user_categories(current_user.id)
    flux = rss_business.get_user_flux(current_user.id)
    collections, _ = collection_business.get_user_collections(
        current_user.id,
        include_shared=True,
        only_owned=False,
        page=1,
        page_size=100
    )
    
    filters = {
        "categories": [{"id": c.id, "name": c.nom} for c in categories],
        "flux": [{"id": f.id, "name": f.nom} for f in flux],
        "collections": [{"id": c.id, "name": c.nom} for c in collections],
        "types": ["articles", "flux", "collections", "comments"],
        "date_ranges": [
            {"value": "today", "label": "Aujourd'hui"},
            {"value": "week", "label": "Cette semaine"},
            {"value": "month", "label": "Ce mois"},
            {"value": "year", "label": "Cette année"},
            {"value": "custom", "label": "Personnalisé"}
        ]
    }
    
    return filters