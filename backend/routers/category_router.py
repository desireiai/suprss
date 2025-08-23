# routers/category_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from dtos.category_dto import (
    CategoryCreateDTO,
    CategoryUpdateDTO,
    CategoryResponseDTO,
    CategoryFluxMoveDTO
)
from business.category_business import CategoryBusiness
from routers.user_router import get_current_user
from core.database import get_db

router = APIRouter(prefix="/api/categories", tags=["Catégories"])

@router.post("/", response_model=CategoryResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée une nouvelle catégorie pour l'utilisateur"""
    category_business = CategoryBusiness(db)
    
    # Vérifier l'unicité du nom pour cet utilisateur
    if category_business.category_name_exists(current_user.id, category_data.nom):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une catégorie avec ce nom existe déjà"
        )
    
    # Créer la catégorie
    category = category_business.create_category(
        user_id=current_user.id,
        category_data=category_data
    )
    
    return category

@router.get("/", response_model=List[CategoryResponseDTO])
async def get_user_categories(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère toutes les catégories de l'utilisateur"""
    category_business = CategoryBusiness(db)
    
    categories = category_business.get_user_categories(current_user.id)
    
    # Ajouter le nombre de flux pour chaque catégorie
    for category in categories:
        category.nombre_flux = category_business.get_category_flux_count(
            current_user.id,
            category.id
        )
    
    return categories

# @router.get("/{category_id}", response_model=CategoryResponseDTO)
# async def get_category_detail(
#     category_id: int,
#     current_user = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Récupère les détails d'une catégorie"""
#     category_business = CategoryBusiness(db)
    
#     category = category_business.get_category_by_id(category_id)
    
#     if not category:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Catégorie non trouvée"
#         )
    
#     # Vérifier que la catégorie appartient à l'utilisateur
#     if not category_business.user_owns_category(current_user.id, category_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Vous n'avez pas accès à cette catégorie"
#         )
    
#     # Ajouter le nombre de flux
#     category.nombre_flux = category_business.get_category_flux_count(
#         current_user.id,
#         category.id
#     )
    
#     return category

@router.put("/{category_id}", response_model=CategoryResponseDTO)
async def update_category(
    category_id: int,
    category_update: CategoryUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour une catégorie"""
    category_business = CategoryBusiness(db)
    
    # Vérifier que la catégorie appartient à l'utilisateur
    if not category_business.user_owns_category(current_user.id, category_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette catégorie"
        )
    
    # Vérifier que ce n'est pas la catégorie par défaut
    if category_business.is_default_category(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La catégorie 'Non classé' ne peut pas être modifiée"
        )
    
    # Vérifier l'unicité du nouveau nom si changement
    if category_update.nom:
        if category_business.category_name_exists(
            current_user.id,
            category_update.nom,
            exclude_id=category_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une catégorie avec ce nom existe déjà"
            )
    
    # Mettre à jour la catégorie
    updated_category = category_business.update_category(
        category_id,
        category_update
    )
    
    # Ajouter le nombre de flux
    updated_category.nombre_flux = category_business.get_category_flux_count(
        current_user.id,
        updated_category.id
    )
    
    return updated_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    move_to_category_id: int = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime une catégorie.
    Si move_to_category_id est fourni, les flux sont déplacés vers cette catégorie.
    Sinon, ils sont déplacés vers la catégorie par défaut.
    """
    category_business = CategoryBusiness(db)
    
    # Vérifier que la catégorie appartient à l'utilisateur
    if not category_business.user_owns_category(current_user.id, category_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette catégorie"
        )
    
    # Vérifier que ce n'est pas la catégorie par défaut
    if category_business.is_default_category(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La catégorie 'Non classé' ne peut pas être supprimée"
        )
    
    # Si une catégorie de destination est fournie, vérifier qu'elle appartient à l'utilisateur
    if move_to_category_id:
        if not category_business.user_owns_category(current_user.id, move_to_category_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La catégorie de destination ne vous appartient pas"
            )
    
    # Supprimer la catégorie (les flux seront déplacés automatiquement)
    category_business.delete_category(
        category_id,
        move_to_category_id=move_to_category_id,
        user_id=current_user.id
    )
    
    return None

# @router.post("/move-flux", status_code=status.HTTP_204_NO_CONTENT)
# async def move_flux_between_categories(
#     move_data: CategoryFluxMoveDTO,
#     current_user = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Déplace un flux d'une catégorie à une autre"""
#     category_business = CategoryBusiness(db)
#     from business_models.rss_business import RSSBusiness
#     rss_business = RSSBusiness(db)
    
#     # Vérifier que le flux appartient à l'utilisateur
#     if not rss_business.user_owns_flux(current_user.id, move_data.flux_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Vous n'avez pas accès à ce flux"
#         )
    
#     # Vérifier les catégories source et destination
#     if move_data.from_category_id:
#         if not category_business.user_owns_category(current_user.id, move_data.from_category_id):
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="La catégorie source ne vous appartient pas"
#             )
    
#     if not category_business.user_owns_category(current_user.id, move_data.to_category_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="La catégorie de destination ne vous appartient pas"
#         )
    
#     # Déplacer le flux
#     category_business.move_flux_to_category(
#         flux_id=move_data.flux_id,
#         from_category_id=move_data.from_category_id,
#         to_category_id=move_data.to_category_id
#     )
    
#     return None

# """ @router.get("/{category_id}/flux", response_model=List[dict])
# async def get_category_flux(
#     category_id: int,
#     current_user = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Récupère tous les flux d'une catégorie"""
#     category_business = CategoryBusiness(db)
#     from business_models.rss_business import RSSBusiness
#     rss_business = RSSBusiness(db)
    
#     # Vérifier que la catégorie appartient à l'utilisateur
#     if not category_business.user_owns_category(current_user.id, category_id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Vous n'avez pas accès à cette catégorie"
#         )
    
#     # Récupérer les flux de la catégorie
#     flux_list = rss_business.get_user_flux(
#         user_id=current_user.id,
#         categorie_id=category_id
#     )
    
#     return flux_list """

# """ @router.post("/initialize-default", response_model=CategoryResponseDTO)
# async def initialize_default_category(
#     current_user = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Initialise la catégorie par défaut pour un nouvel utilisateur.
#     Cette route est appelée automatiquement lors de la première connexion.
#     """
#     category_business = CategoryBusiness(db)
    
#     # Vérifier si l'utilisateur a déjà une catégorie par défaut
#     default_category = category_business.get_user_default_category(current_user.id)
    
#     if default_category:
#         return default_category
    
#     # Créer la catégorie par défaut
#     default_category = category_business.create_default_category(current_user.id)
    
#     return default_category """

