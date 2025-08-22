# routers/collection_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from dto.collection_dto import (
    CollectionCreateDTO,
    CollectionUpdateDTO,
    CollectionFluxAddDTO,
    CollectionMemberAddDTO,
    CollectionMemberUpdateDTO,
    CollectionMemberResponseDTO,
    CollectionResponseDTO,
    CollectionDetailResponseDTO
)
from dto.pagination_dto import PaginationParamsDTO, PaginatedResponseDTO
from business_models.collection_business import CollectionBusiness
from routers.user_router import get_current_user
from core.database import get_db

router = APIRouter(prefix="/api/collections", tags=["Collections"])

@router.post("/", response_model=CollectionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée une nouvelle collection"""
    collection_business = CollectionBusiness(db)
    
    # Créer la collection
    collection = collection_business.create_collection(
        user_id=current_user.id,
        collection_data=collection_data
    )
    
    return collection

@router.get("/", response_model=PaginatedResponseDTO[CollectionResponseDTO])
async def get_user_collections(
    pagination: PaginationParamsDTO = Depends(),
    include_shared: bool = Query(True, description="Inclure les collections partagées"),
    only_owned: bool = Query(False, description="Uniquement mes collections"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les collections de l'utilisateur"""
    collection_business = CollectionBusiness(db)
    
    collections, total = collection_business.get_user_collections(
        user_id=current_user.id,
        include_shared=include_shared,
        only_owned=only_owned,
        page=pagination.page,
        page_size=pagination.page_size
    )
    
    # Ajouter les permissions et rôle pour chaque collection
    for collection in collections:
        collection.mon_role = collection_business.get_user_role_in_collection(
            current_user.id,
            collection.id
        )
        collection.mes_permissions = collection_business.get_user_permissions(
            current_user.id,
            collection.id
        )
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponseDTO(
        items=collections,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_previous=pagination.page > 1
    )

@router.get("/{collection_id}", response_model=CollectionDetailResponseDTO)
async def get_collection_detail(
    collection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les détails d'une collection"""
    collection_business = CollectionBusiness(db)
    
    # Vérifier l'accès à la collection
    if not collection_business.user_can_read_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette collection"
        )
    
    collection = collection_business.get_collection_detail(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection non trouvée"
        )
    
    # Ajouter les permissions et rôle
    collection.mon_role = collection_business.get_user_role_in_collection(
        current_user.id,
        collection.id
    )
    collection.mes_permissions = collection_business.get_user_permissions(
        current_user.id,
        collection.id
    )
    
    return collection

@router.put("/{collection_id}", response_model=CollectionResponseDTO)
async def update_collection(
    collection_id: int,
    collection_update: CollectionUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour une collection"""
    collection_business = CollectionBusiness(db)
    
    # Vérifier les permissions de modification
    if not collection_business.user_can_modify_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de modifier cette collection"
        )
    
    updated_collection = collection_business.update_collection(
        collection_id,
        collection_update
    )
    
    return updated_collection

@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime une collection (seul le propriétaire peut supprimer)"""
    collection_business = CollectionBusiness(db)
    
    # Vérifier que l'utilisateur est le propriétaire
    if not collection_business.user_owns_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire peut supprimer une collection"
        )
    
    collection_business.delete_collection(collection_id)
    return None

@router.post("/{collection_id}/flux", status_code=status.HTTP_204_NO_CONTENT)
async def add_flux_to_collection(
    collection_id: int,
    flux_data: CollectionFluxAddDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ajoute un flux à une collection"""
    collection_business = CollectionBusiness(db)
    from business_models.rss_business import RSSBusiness
    rss_business = RSSBusiness(db)
    
    # Vérifier la permission d'ajouter des flux
    if not collection_business.user_can_add_flux(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'ajouter des flux à cette collection"
        )
    
    # Vérifier que le flux appartient à l'utilisateur
    if not rss_business.user_owns_flux(current_user.id, flux_data.flux_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce flux ne vous appartient pas"
        )
    
    # Ajouter le flux à la collection
    collection_business.add_flux_to_collection(
        collection_id,
        flux_data.flux_id
    )
    
    return None

@router.delete("/{collection_id}/flux/{flux_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_flux_from_collection(
    collection_id: int,
    flux_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retire un flux d'une collection"""
    collection_business = CollectionBusiness(db)
    
    # Vérifier la permission de supprimer
    if not collection_business.user_can_delete_in_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de retirer des flux de cette collection"
        )
    
    collection_business.remove_flux_from_collection(collection_id, flux_id)
    return None

@router.post("/{collection_id}/members", response_model=CollectionMemberResponseDTO)
async def add_member_to_collection(
    collection_id: int,
    member_data: CollectionMemberAddDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ajoute un membre à une collection"""
    collection_business = CollectionBusiness(db)
    
    # Seuls les propriétaires et administrateurs peuvent ajouter des membres
    user_role = collection_business.get_user_role_in_collection(
        current_user.id,
        collection_id
    )
    
    if user_role not in ["proprietaire", "administrateur"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires et administrateurs peuvent ajouter des membres"
        )
    
    # Si invitation par email, vérifier que l'utilisateur existe
    if member_data.email:
        from business_models.user_business import UserBusiness
        user_business = UserBusiness(db)
        invited_user = user_business.get_user_by_email(member_data.email)
        
        if not invited_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun utilisateur trouvé avec cet email"
            )
        member_data.utilisateur_id = invited_user.id
    
    # Vérifier que l'utilisateur n'est pas déjà membre
    if collection_business.is_user_member(member_data.utilisateur_id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur est déjà membre de la collection"
        )
    
    # Ajouter le membre
    member = collection_business.add_member_to_collection(
        collection_id,
        member_data
    )
    
    return member

@router.put("/{collection_id}/members/{member_id}", response_model=CollectionMemberResponseDTO)
async def update_member_permissions(
    collection_id: int,
    member_id: int,
    member_update: CollectionMemberUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour les permissions d'un membre"""
    collection_business = CollectionBusiness(db)
    
    # Seuls les propriétaires et administrateurs peuvent modifier les permissions
    user_role = collection_business.get_user_role_in_collection(
        current_user.id,
        collection_id
    )
    
    if user_role not in ["proprietaire", "administrateur"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires et administrateurs peuvent modifier les permissions"
        )
    
    # Le propriétaire ne peut pas être modifié
    if collection_business.is_member_owner(member_id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Les permissions du propriétaire ne peuvent pas être modifiées"
        )
    
    # Mettre à jour les permissions
    updated_member = collection_business.update_member_permissions(
        collection_id,
        member_id,
        member_update
    )
    
    return updated_member

@router.delete("/{collection_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_collection(
    collection_id: int,
    member_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retire un membre de la collection"""
    collection_business = CollectionBusiness(db)
    
    # Vérifier les permissions
    user_role = collection_business.get_user_role_in_collection(
        current_user.id,
        collection_id
    )
    
    # Un membre peut se retirer lui-même
    member_user_id = collection_business.get_member_user_id(member_id)
    if member_user_id == current_user.id:
        # Un membre peut quitter la collection (sauf le propriétaire)
        if collection_business.is_member_owner(member_id, collection_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le propriétaire ne peut pas quitter sa propre collection"
            )
    else:
        # Sinon, seuls les propriétaires et administrateurs peuvent retirer des membres
        if user_role not in ["proprietaire", "administrateur"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas la permission de retirer des membres"
            )
        
        # Le propriétaire ne peut pas être retiré
        if collection_business.is_member_owner(member_id, collection_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le propriétaire ne peut pas être retiré de la collection"
            )
    
    collection_business.remove_member_from_collection(member_id)
    return None

@router.get("/{collection_id}/members", response_model=List[CollectionMemberResponseDTO])
async def get_collection_members(
    collection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère la liste des membres d'une collection"""
    collection_business = CollectionBusiness(db)
    
    # Vérifier l'accès à la collection
    if not collection_business.user_can_read_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette collection"
        )
    
    members = collection_business.get_collection_members(collection_id)
    return members

@router.post("/{collection_id}/toggle-sharing", response_model=CollectionResponseDTO)
async def toggle_collection_sharing(
    collection_id: int,
    is_shared: bool,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Active ou désactive le partage d'une collection"""
    collection_business = CollectionBusiness(db)
    
    # Seul le propriétaire peut changer le statut de partage
    if not collection_business.user_owns_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le propriétaire peut modifier le statut de partage"
        )
    
    updated_collection = collection_business.toggle_sharing(collection_id, is_shared)
    return updated_collection

@router.get("/{collection_id}/invitations", response_model=List[dict])
async def get_pending_invitations(
    collection_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les invitations en attente pour une collection"""
    collection_business = CollectionBusiness(db)
    
    # Seuls les propriétaires et administrateurs peuvent voir les invitations
    user_role = collection_business.get_user_role_in_collection(
        current_user.id,
        collection_id
    )
    
    if user_role not in ["proprietaire", "administrateur"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les propriétaires et administrateurs peuvent voir les invitations"
        )
    
    invitations = collection_business.get_pending_invitations(collection_id)
    return invitations