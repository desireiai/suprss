# routers/interaction_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from dto.interaction_dto import (
    CommentCreateDTO,
    CommentUpdateDTO,
    CommentResponseDTO,
    MessageCreateDTO,
    MessageResponseDTO,
    NotificationDTO
)
from dto.pagination_dto import PaginationParamsDTO, PaginatedResponseDTO
from business_models.interaction_business import InteractionBusiness
from business_models.collection_business import CollectionBusiness
from routers.user_router import get_current_user
from core.database import get_db
from core.websocket_manager import ConnectionManager

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])

# Gestionnaire WebSocket pour le chat en temps réel
manager = ConnectionManager()

@router.post("/comments", response_model=CommentResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée un nouveau commentaire sur un article"""
    interaction_business = InteractionBusiness(db)
    collection_business = CollectionBusiness(db)
    
    # Vérifier l'accès à la collection
    if not collection_business.user_can_read_collection(
        current_user.id,
        comment_data.collection_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette collection"
        )
    
    # Vérifier la permission de commenter
    if not collection_business.user_can_comment_in_collection(
        current_user.id,
        comment_data.collection_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de commenter dans cette collection"
        )
    
    # Vérifier que l'article appartient à la collection
    if not interaction_business.article_belongs_to_collection(
        comment_data.article_id,
        comment_data.collection_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet article n'appartient pas à cette collection"
        )
    
    # Si c'est une réponse, vérifier que le commentaire parent existe
    if comment_data.commentaire_parent_id:
        parent_comment = interaction_business.get_comment_by_id(
            comment_data.commentaire_parent_id
        )
        if not parent_comment or parent_comment.article_id != comment_data.article_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Commentaire parent invalide"
            )
    
    # Créer le commentaire
    comment = interaction_business.create_comment(
        user_id=current_user.id,
        comment_data=comment_data
    )
    
    # Notifier les membres de la collection
    interaction_business.notify_new_comment(
        comment_id=comment.id,
        collection_id=comment_data.collection_id,
        author_id=current_user.id
    )
    
    return comment

@router.get("/comments/article/{article_id}", response_model=List[CommentResponseDTO])
async def get_article_comments(
    article_id: int,
    collection_id: int = Query(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère tous les commentaires d'un article"""
    interaction_business = InteractionBusiness(db)
    collection_business = CollectionBusiness(db)
    
    # Vérifier l'accès à la collection
    if not collection_business.user_can_read_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette collection"
        )
    
    # Récupérer les commentaires avec leurs réponses
    comments = interaction_business.get_article_comments(
        article_id=article_id,
        collection_id=collection_id
    )
    
    return comments

@router.put("/comments/{comment_id}", response_model=CommentResponseDTO)
async def update_comment(
    comment_id: int,
    comment_update: CommentUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour un commentaire (seul l'auteur peut modifier)"""
    interaction_business = InteractionBusiness(db)
    
    comment = interaction_business.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commentaire non trouvé"
        )
    
    # Vérifier que l'utilisateur est l'auteur
    if comment.utilisateur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez modifier que vos propres commentaires"
        )
    
    # Mettre à jour le commentaire
    updated_comment = interaction_business.update_comment(
        comment_id,
        comment_update
    )
    
    return updated_comment

@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime un commentaire (soft delete)"""
    interaction_business = InteractionBusiness(db)
    collection_business = CollectionBusiness(db)
    
    comment = interaction_business.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commentaire non trouvé"
        )
    
    # L'auteur peut supprimer son commentaire
    # Les modérateurs et administrateurs peuvent aussi supprimer
    can_delete = False
    
    if comment.utilisateur_id == current_user.id:
        can_delete = True
    else:
        user_role = collection_business.get_user_role_in_collection(
            current_user.id,
            comment.collection_id
        )
        if user_role in ["proprietaire", "administrateur", "moderateur"]:
            can_delete = True
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de supprimer ce commentaire"
        )
    
    # Soft delete (marquer comme supprimé plutôt que supprimer réellement)
    interaction_business.soft_delete_comment(comment_id)
    
    return None

@router.post("/messages", response_model=MessageResponseDTO, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Envoie un message dans le chat d'une collection"""
    interaction_business = InteractionBusiness(db)
    collection_business = CollectionBusiness(db)
    
    # Vérifier l'accès à la collection
    if not collection_business.user_can_read_collection(
        current_user.id,
        message_data.collection_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette collection"
        )
    
    # Créer le message
    message = interaction_business.create_message(
        user_id=current_user.id,
        message_data=message_data
    )
    
    # Diffuser le message via WebSocket aux membres connectés
    await manager.broadcast_to_collection(
        collection_id=message_data.collection_id,
        message=message.dict()
    )
    
    return message

@router.get("/messages/collection/{collection_id}", response_model=PaginatedResponseDTO[MessageResponseDTO])
async def get_collection_messages(
    collection_id: int,
    pagination: PaginationParamsDTO = Depends(),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les messages d'une collection avec pagination"""
    interaction_business = InteractionBusiness(db)
    collection_business = CollectionBusiness(db)
    
    # Vérifier l'accès à la collection
    if not collection_business.user_can_read_collection(current_user.id, collection_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette collection"
        )
    
    # Récupérer les messages
    messages, total = interaction_business.get_collection_messages(
        collection_id=collection_id,
        page=pagination.page,
        page_size=pagination.page_size
    )
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponseDTO(
        items=messages,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
        has_next=pagination.page < total_pages,
        has_previous=pagination.page > 1
    )

@router.get("/notifications", response_model=List[NotificationDTO])
async def get_user_notifications(
    only_unread: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les notifications de l'utilisateur"""
    interaction_business = InteractionBusiness(db)
    
    notifications = interaction_business.get_user_notifications(
        user_id=current_user.id,
        only_unread=only_unread,
        limit=limit
    )
    
    return notifications

@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marque une notification comme lue"""
    interaction_business = InteractionBusiness(db)
    
    # Vérifier que la notification appartient à l'utilisateur
    notification = interaction_business.get_notification_by_id(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification non trouvée"
        )
    
    if notification.utilisateur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette notification ne vous appartient pas"
        )
    
    interaction_business.mark_notification_as_read(notification_id)
    
    return None

@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marque toutes les notifications comme lues"""
    interaction_business = InteractionBusiness(db)
    
    interaction_business.mark_all_notifications_as_read(current_user.id)
    
    return None

@router.get("/notifications/count", response_model=dict)
async def get_unread_notifications_count(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère le nombre de notifications non lues"""
    interaction_business = InteractionBusiness(db)
    
    count = interaction_business.get_unread_notifications_count(current_user.id)
    
    return {"unread_count": count}

# WebSocket pour le chat en temps réel
@router.websocket("/ws/collection/{collection_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    collection_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket pour le chat en temps réel d'une collection"""
    try:
        # Vérifier le token et récupérer l'utilisateur
        from core.security import verify_token
        payload = verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            await websocket.close(code=1008, reason="Token invalide")
            return
        
        # Vérifier l'accès à la collection
        collection_business = CollectionBusiness(db)
        if not collection_business.user_can_read_collection(user_id, collection_id):
            await websocket.close(code=1008, reason="Accès refusé")
            return
        
        # Accepter la connexion
        await manager.connect(websocket, collection_id, user_id)
        
        try:
            while True:
                # Recevoir et diffuser les messages
                data = await websocket.receive_text()
                
                # Créer le message dans la base de données
                interaction_business = InteractionBusiness(db)
                message_data = MessageCreateDTO(
                    collection_id=collection_id,
                    contenu=data
                )
                message = interaction_business.create_message(user_id, message_data)
                
                # Diffuser à tous les membres connectés
                await manager.broadcast_to_collection(
                    collection_id=collection_id,
                    message=message.dict(),
                    exclude_websocket=websocket
                )
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, collection_id)
            
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

@router.get("/comments/my-comments", response_model=List[CommentResponseDTO])
async def get_my_comments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère tous les commentaires de l'utilisateur"""
    interaction_business = InteractionBusiness(db)
    
    comments = interaction_business.get_user_comments(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    return comments

@router.get("/activity/recent", response_model=List[dict])
async def get_recent_activity(
    collection_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère l'activité récente (commentaires et messages)"""
    interaction_business = InteractionBusiness(db)
    
    # Si une collection est spécifiée, vérifier l'accès
    if collection_id:
        collection_business = CollectionBusiness(db)
        if not collection_business.user_can_read_collection(current_user.id, collection_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à cette collection"
            )
    
    activity = interaction_business.get_recent_activity(
        user_id=current_user.id,
        collection_id=collection_id,
        limit=limit
    )
    
    return activity