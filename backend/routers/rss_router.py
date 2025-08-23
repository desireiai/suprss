# routers/rss_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from dtos.rss_dto import (
    FluxCreateDTO,
    FluxUpdateDTO,
    FluxResponseDTO,
    ArticleResponseDTO,
    ArticleStatusUpdateDTO,
    ArticleFilterDTO,
    ArticleBulkActionDTO
)
from dtos.pagination_dto import PaginationParamsDTO, PaginatedResponseDTO
from business.rss_business import RssBusiness
from routers.user_router import get_current_user
from core.database import get_db

router = APIRouter(prefix="/api/rss", tags=["Flux RSS"])

@router.post("/flux", response_model=FluxResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_flux(
    flux_data: FluxCreateDTO,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ajoute un nouveau flux RSS pour l'utilisateur"""
    rss_business = RssBusiness(db)
    
    # Vérifier si le flux existe déjà pour cet utilisateur
    if rss_business.flux_exists_for_user(current_user.id, str(flux_data.url)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà ajouté ce flux RSS"
        )
    
    # Créer le flux
    flux = rss_business.create_flux(
        user_id=current_user.id,
        flux_data=flux_data
    )
    
    # Lancer la récupération des articles en arrière-plan
    background_tasks.add_task(
        rss_business.fetch_flux_articles,
        flux.id
    )
    
    return flux

@router.get("/flux", response_model=List[FluxResponseDTO])
async def get_user_flux(
    categorie_id: Optional[int] = None,
    est_actif: Optional[bool] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère tous les flux de l'utilisateur"""
    rss_business = RssBusiness(db)
    
    flux_list = rss_business.get_user_flux(
        user_id=current_user.id,
        categorie_id=categorie_id,
        est_actif=est_actif
    )
    
    return flux_list

@router.get("/flux/{flux_id}", response_model=FluxResponseDTO)
async def get_flux_detail(
    flux_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'un flux"""
    rss_business = RssBusiness(db)
    
    flux = rss_business.get_flux_by_id(flux_id)
    
    if not flux:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flux non trouvé"
        )
    
    # Vérifier que le flux appartient à l'utilisateur
    if not rss_business.user_owns_flux(current_user.id, flux_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce flux"
        )
    
    return flux

@router.put("/flux/{flux_id}", response_model=FluxResponseDTO)
async def update_flux(
    flux_id: int,
    flux_update: FluxUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour un flux RSS"""
    rss_business = RssBusiness(db)
    
    # Vérifier que le flux appartient à l'utilisateur
    if not rss_business.user_owns_flux(current_user.id, flux_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce flux"
        )
    
    updated_flux = rss_business.update_flux(flux_id, flux_update)
    return updated_flux

@router.delete("/flux/{flux_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flux(
    flux_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime un flux RSS"""
    rss_business = RssBusiness(db)
    
    # Vérifier que le flux appartient à l'utilisateur
    if not rss_business.user_owns_flux(current_user.id, flux_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce flux"
        )
    
    rss_business.delete_flux(flux_id)
    return None

@router.post("/flux/{flux_id}/refresh", status_code=status.HTTP_202_ACCEPTED)
async def refresh_flux(
    flux_id: int,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Force la mise à jour d'un flux RSS"""
    rss_business = RssBusiness(db)
    
    # Vérifier que le flux appartient à l'utilisateur
    if not rss_business.user_owns_flux(current_user.id, flux_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à ce flux"
        )
    
    # Vérifier la fréquence de mise à jour
    if not rss_business.can_refresh_flux(flux_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Veuillez attendre avant de rafraîchir ce flux"
        )
    
    # Lancer la mise à jour en arrière-plan
    background_tasks.add_task(
        rss_business.fetch_flux_articles,
        flux_id
    )
    
    return {"message": "Mise à jour en cours"}

@router.get("/articles", response_model=PaginatedResponseDTO[ArticleResponseDTO])
async def get_articles(
    pagination: PaginationParamsDTO = Depends(),
    categorie_id: Optional[int] = Query(None),
    flux_id: Optional[int] = Query(None),
    only_unread: bool = Query(False),
    only_favorites: bool = Query(False),
    search_query: Optional[str] = Query(None),
    date_debut: Optional[datetime] = Query(None),
    date_fin: Optional[datetime] = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les articles avec filtres et pagination"""
    rss_business = RssBusiness(db)
    
    # Créer le filtre
    filter_dto = ArticleFilterDTO(
        categorie_id=categorie_id,
        flux_id=flux_id,
        only_unread=only_unread,
        only_favorites=only_favorites,
        search_query=search_query,
        date_debut=date_debut,
        date_fin=date_fin,
        limit=pagination.page_size,
        offset=(pagination.page - 1) * pagination.page_size
    )
    
    # Récupérer les articles
    articles, total = rss_business.get_user_articles(
        user_id=current_user.id,
        filters=filter_dto,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order
    )
    
    # Calculer les métadonnées de pagination
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponseDTO(
        items=articles,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_previous=pagination.page > 1
    )

@router.get("/articles/{article_id}", response_model=ArticleResponseDTO)
async def get_article_detail(
    article_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'un article"""
    rss_business = RssBusiness(db)
    
    article = rss_business.get_article_by_id(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article non trouvé"
        )
    
    # Vérifier que l'utilisateur a accès à cet article
    if not rss_business.user_can_read_article(current_user.id, article_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cet article"
        )
    
    # Marquer automatiquement comme lu
    rss_business.mark_article_as_read(current_user.id, article_id)
    
    return article

@router.patch("/articles/{article_id}/status", response_model=ArticleResponseDTO)
async def update_article_status(
    article_id: int,
    status_update: ArticleStatusUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour le statut d'un article (lu/favori)"""
    rss_business = RssBusiness(db)
    
    # Vérifier que l'utilisateur a accès à cet article
    if not rss_business.user_can_read_article(current_user.id, article_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cet article"
        )
    
    # Mettre à jour le statut
    if status_update.est_lu is not None:
        if status_update.est_lu:
            rss_business.mark_article_as_read(current_user.id, article_id)
        else:
            rss_business.mark_article_as_unread(current_user.id, article_id)
    
    if status_update.est_favori is not None:
        if status_update.est_favori:
            rss_business.add_article_to_favorites(current_user.id, article_id)
        else:
            rss_business.remove_article_from_favorites(current_user.id, article_id)
    
    # Retourner l'article mis à jour
    article = rss_business.get_article_by_id(article_id)
    return article

@router.post("/articles/bulk-action", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_article_action(
    bulk_action: ArticleBulkActionDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Effectue une action en masse sur plusieurs articles"""
    rss_business = RssBusiness(db)
    
    # Vérifier l'accès à tous les articles
    for article_id in bulk_action.article_ids:
        if not rss_business.user_can_read_article(current_user.id, article_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous n'avez pas accès à l'article {article_id}"
            )
    
    # Effectuer l'action
    if bulk_action.action == "mark_read":
        rss_business.mark_articles_as_read(current_user.id, bulk_action.article_ids)
    elif bulk_action.action == "mark_unread":
        rss_business.mark_articles_as_unread(current_user.id, bulk_action.article_ids)
    elif bulk_action.action == "add_favorite":
        rss_business.add_articles_to_favorites(current_user.id, bulk_action.article_ids)
    elif bulk_action.action == "remove_favorite":
        rss_business.remove_articles_from_favorites(current_user.id, bulk_action.article_ids)
    
    return None

@router.get("/articles/favorites", response_model=List[ArticleResponseDTO])
async def get_favorite_articles(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les articles favoris de l'utilisateur"""
    rss_business = RssBusiness(db)
    
    favorites = rss_business.get_user_favorites(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    return favorites

@router.get("/articles/unread/count", response_model=dict)
async def get_unread_count(
    categorie_id: Optional[int] = None,
    flux_id: Optional[int] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère le nombre d'articles non lus"""
    rss_business = RssBusiness(db)
    
    count = rss_business.get_unread_count(
        user_id=current_user.id,
        categorie_id=categorie_id,
        flux_id=flux_id
    )
    
    return {"unread_count": count}

@router.post("/flux/import-opml", response_model=dict, status_code=status.HTTP_201_CREATED)
async def import_opml(
    opml_file: bytes,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Importe des flux depuis un fichier OPML"""
    rss_business = RssBusiness(db)
    
    try:
        imported_count = rss_business.import_opml(
            user_id=current_user.id,
            opml_content=opml_file
        )
        
        # Lancer la récupération des articles en arrière-plan
        background_tasks.add_task(
            rss_business.fetch_all_user_flux_articles,
            current_user.id
        )
        
        return {
            "message": f"{imported_count} flux importés avec succès",
            "imported_count": imported_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de l'import OPML: {str(e)}"
        )

@router.get("/flux/export-opml", response_class=str)
async def export_opml(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporte les flux de l'utilisateur au format OPML"""
    rss_business = RssBusiness(db)
    
    opml_content = rss_business.export_to_opml(current_user.id)
    
    return opml_content