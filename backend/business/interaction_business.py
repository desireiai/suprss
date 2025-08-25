# business/interaction_business.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import logging

# Imports corrigés pour correspondre à votre structure
from models import (
    CommentaireArticle,
    MessageCollection,
    Utilisateur,
    Article,
    Collection,
    CollectionFlux,
    MembreCollection
)
from dtos.interaction_dto import (
    CommentCreateDTO,
    CommentUpdateDTO,
    CommentResponseDTO,
    MessageCreateDTO,
    MessageResponseDTO
)

logger = logging.getLogger(__name__)

class InteractionBusiness:
    """Logique métier pour la gestion des interactions (commentaires et messages uniquement)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_comment(self, user_id: int, comment_data: CommentCreateDTO) -> CommentResponseDTO:
        """Créer un nouveau commentaire"""
        try:
            comment = CommentaireArticle(
                article_id=comment_data.article_id,
                utilisateur_id=user_id,
                collection_id=comment_data.collection_id,
                contenu=comment_data.contenu,
                commentaire_parent_id=comment_data.commentaire_parent_id,
                cree_le=datetime.utcnow(),
                modifie_le=datetime.utcnow()
            )
            
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)
            
            # Récupérer le nom de l'utilisateur
            utilisateur_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == user_id
            ).scalar() or "Utilisateur inconnu"
            
            return CommentResponseDTO(
                id=comment.id,
                article_id=comment.article_id,
                utilisateur_id=comment.utilisateur_id,
                utilisateur_nom=utilisateur_nom,
                collection_id=comment.collection_id,
                contenu=comment.contenu,
                commentaire_parent_id=comment.commentaire_parent_id,
                est_modifie=False,
                cree_le=comment.cree_le,
                modifie_le=comment.modifie_le,
                reponses=[]
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création du commentaire: {e}")
            raise
    
    def article_belongs_to_collection(self, article_id: int, collection_id: int) -> bool:
        """Vérifier qu'un article appartient à une collection"""
        # Un article appartient à une collection si son flux fait partie de la collection
        exists = self.db.query(Article).join(
            CollectionFlux, Article.flux_id == CollectionFlux.flux_id
        ).filter(
            Article.id == article_id,
            CollectionFlux.collection_id == collection_id
        ).first()
        
        return exists is not None
    
    def get_comment_by_id(self, comment_id: int) -> Optional[CommentaireArticle]:
        """Récupérer un commentaire par son ID"""
        return self.db.query(CommentaireArticle).filter(
            CommentaireArticle.id == comment_id
        ).first()
    
    def notify_new_comment(self, comment_id: int, collection_id: int, author_id: int):
        """Log du nouveau commentaire (sans notifications en BDD)"""
        logger.info(f"Nouveau commentaire {comment_id} dans la collection {collection_id} par {author_id}")
    
    def get_article_comments(self, article_id: int, collection_id: int) -> List[CommentResponseDTO]:
        """Récupérer tous les commentaires d'un article avec leurs réponses"""
        # Récupérer les commentaires principaux (sans parent)
        main_comments = self.db.query(
            CommentaireArticle.id,
            CommentaireArticle.article_id,
            CommentaireArticle.utilisateur_id,
            CommentaireArticle.collection_id,
            CommentaireArticle.contenu,
            CommentaireArticle.commentaire_parent_id,
            CommentaireArticle.cree_le,
            CommentaireArticle.modifie_le,
            Utilisateur.nom_utilisateur
        ).join(
            Utilisateur, CommentaireArticle.utilisateur_id == Utilisateur.id
        ).filter(
            CommentaireArticle.article_id == article_id,
            CommentaireArticle.collection_id == collection_id,
            CommentaireArticle.commentaire_parent_id.is_(None)
        ).order_by(CommentaireArticle.cree_le.asc()).all()
        
        # Récupérer toutes les réponses
        replies = self.db.query(
            CommentaireArticle.id,
            CommentaireArticle.article_id,
            CommentaireArticle.utilisateur_id,
            CommentaireArticle.collection_id,
            CommentaireArticle.contenu,
            CommentaireArticle.commentaire_parent_id,
            CommentaireArticle.cree_le,
            CommentaireArticle.modifie_le,
            Utilisateur.nom_utilisateur
        ).join(
            Utilisateur, CommentaireArticle.utilisateur_id == Utilisateur.id
        ).filter(
            CommentaireArticle.article_id == article_id,
            CommentaireArticle.collection_id == collection_id,
            CommentaireArticle.commentaire_parent_id.is_not(None)
        ).order_by(CommentaireArticle.cree_le.asc()).all()
        
        # Organiser les réponses par commentaire parent
        replies_by_parent = {}
        for reply in replies:
            parent_id = reply.commentaire_parent_id
            if parent_id not in replies_by_parent:
                replies_by_parent[parent_id] = []
            
            # Vérifier si le commentaire a été modifié
            est_modifie = reply.modifie_le and reply.modifie_le > reply.cree_le
            
            replies_by_parent[parent_id].append(CommentResponseDTO(
                id=reply.id,
                article_id=reply.article_id,
                utilisateur_id=reply.utilisateur_id,
                utilisateur_nom=reply.nom_utilisateur,
                collection_id=reply.collection_id,
                contenu=reply.contenu,
                commentaire_parent_id=reply.commentaire_parent_id,
                est_modifie=est_modifie,
                cree_le=reply.cree_le,
                modifie_le=reply.modifie_le,
                reponses=[]
            ))
        
        # Construire la liste des commentaires avec leurs réponses
        result = []
        for comment in main_comments:
            # Vérifier si le commentaire a été modifié
            est_modifie = comment.modifie_le and comment.modifie_le > comment.cree_le
            
            comment_dto = CommentResponseDTO(
                id=comment.id,
                article_id=comment.article_id,
                utilisateur_id=comment.utilisateur_id,
                utilisateur_nom=comment.nom_utilisateur,
                collection_id=comment.collection_id,
                contenu=comment.contenu,
                commentaire_parent_id=comment.commentaire_parent_id,
                est_modifie=est_modifie,
                cree_le=comment.cree_le,
                modifie_le=comment.modifie_le,
                reponses=replies_by_parent.get(comment.id, [])
            )
            result.append(comment_dto)
        
        return result
    
    def update_comment(self, comment_id: int, comment_update: CommentUpdateDTO) -> CommentResponseDTO:
        """Mettre à jour un commentaire"""
        try:
            comment = self.db.query(CommentaireArticle).filter(
                CommentaireArticle.id == comment_id
            ).first()
            
            if not comment:
                raise ValueError("Commentaire non trouvé")
            
            comment.contenu = comment_update.contenu
            comment.modifie_le = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(comment)
            
            # Récupérer le nom de l'utilisateur
            utilisateur_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == comment.utilisateur_id
            ).scalar() or "Utilisateur inconnu"
            
            return CommentResponseDTO(
                id=comment.id,
                article_id=comment.article_id,
                utilisateur_id=comment.utilisateur_id,
                utilisateur_nom=utilisateur_nom,
                collection_id=comment.collection_id,
                contenu=comment.contenu,
                commentaire_parent_id=comment.commentaire_parent_id,
                est_modifie=True,
                cree_le=comment.cree_le,
                modifie_le=comment.modifie_le,
                reponses=[]
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour du commentaire: {e}")
            raise
    
    def soft_delete_comment(self, comment_id: int):
        """Suppression logique d'un commentaire"""
        try:
            comment = self.db.query(CommentaireArticle).filter(
                CommentaireArticle.id == comment_id
            ).first()
            
            if comment:
                # Marquer le commentaire comme supprimé en modifiant son contenu
                comment.contenu = "[Commentaire supprimé]"
                comment.modifie_le = datetime.utcnow()
                
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression du commentaire: {e}")
            raise
    
    def create_message(self, user_id: int, message_data: MessageCreateDTO) -> MessageResponseDTO:
        """Créer un nouveau message dans une collection"""
        try:
            message = MessageCollection(
                collection_id=message_data.collection_id,
                utilisateur_id=user_id,
                contenu=message_data.contenu,
                cree_le=datetime.utcnow(),
                modifie_le=datetime.utcnow()
            )
            
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            
            # Récupérer le nom de l'utilisateur
            utilisateur_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == user_id
            ).scalar() or "Utilisateur inconnu"
            
            return MessageResponseDTO(
                id=message.id,
                collection_id=message.collection_id,
                utilisateur_id=message.utilisateur_id,
                utilisateur_nom=utilisateur_nom,
                contenu=message.contenu,
                est_modifie=False,
                cree_le=message.cree_le,
                modifie_le=message.modifie_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création du message: {e}")
            raise
    
    def get_collection_messages(
        self, 
        collection_id: int, 
        page: int = 1, 
        page_size: int = 50
    ) -> Tuple[List[MessageResponseDTO], int]:
        """Récupérer les messages d'une collection avec pagination"""
        
        # Compter le total
        total = self.db.query(func.count(MessageCollection.id)).filter(
            MessageCollection.collection_id == collection_id
        ).scalar() or 0
        
        # Récupérer les messages avec pagination
        offset = (page - 1) * page_size
        messages = self.db.query(
            MessageCollection.id,
            MessageCollection.collection_id,
            MessageCollection.utilisateur_id,
            MessageCollection.contenu,
            MessageCollection.cree_le,
            MessageCollection.modifie_le,
            Utilisateur.nom_utilisateur
        ).join(
            Utilisateur, MessageCollection.utilisateur_id == Utilisateur.id
        ).filter(
            MessageCollection.collection_id == collection_id
        ).order_by(
            MessageCollection.cree_le.desc()
        ).offset(offset).limit(page_size).all()
        
        # Convertir en DTOs
        result = []
        for msg in messages:
            est_modifie = msg.modifie_le and msg.modifie_le > msg.cree_le
            
            result.append(MessageResponseDTO(
                id=msg.id,
                collection_id=msg.collection_id,
                utilisateur_id=msg.utilisateur_id,
                utilisateur_nom=msg.nom_utilisateur,
                contenu=msg.contenu,
                est_modifie=est_modifie,
                cree_le=msg.cree_le,
                modifie_le=msg.modifie_le
            ))
        
        return result, total
    
    def get_user_comments(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[CommentResponseDTO]:
        """Récupérer tous les commentaires d'un utilisateur"""
        comments = self.db.query(
            CommentaireArticle.id,
            CommentaireArticle.article_id,
            CommentaireArticle.utilisateur_id,
            CommentaireArticle.collection_id,
            CommentaireArticle.contenu,
            CommentaireArticle.commentaire_parent_id,
            CommentaireArticle.cree_le,
            CommentaireArticle.modifie_le,
            Utilisateur.nom_utilisateur
        ).join(
            Utilisateur, CommentaireArticle.utilisateur_id == Utilisateur.id
        ).filter(
            CommentaireArticle.utilisateur_id == user_id
        ).order_by(
            CommentaireArticle.cree_le.desc()
        ).offset(offset).limit(limit).all()
        
        result = []
        for comment in comments:
            est_modifie = comment.modifie_le and comment.modifie_le > comment.cree_le
            
            result.append(CommentResponseDTO(
                id=comment.id,
                article_id=comment.article_id,
                utilisateur_id=comment.utilisateur_id,
                utilisateur_nom=comment.nom_utilisateur,
                collection_id=comment.collection_id,
                contenu=comment.contenu,
                commentaire_parent_id=comment.commentaire_parent_id,
                est_modifie=est_modifie,
                cree_le=comment.cree_le,
                modifie_le=comment.modifie_le,
                reponses=[]
            ))
        
        return result
    
    def get_recent_activity(
        self, 
        user_id: int, 
        collection_id: Optional[int] = None, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Récupérer l'activité récente (commentaires et messages)"""
        activities = []
        
        # Récupérer les commentaires récents
        comments_query = self.db.query(
            CommentaireArticle.id,
            CommentaireArticle.contenu,
            CommentaireArticle.cree_le,
            CommentaireArticle.collection_id,
            CommentaireArticle.article_id,
            Utilisateur.nom_utilisateur
        ).join(
            Utilisateur, CommentaireArticle.utilisateur_id == Utilisateur.id
        ).join(
            MembreCollection, and_(
                MembreCollection.collection_id == CommentaireArticle.collection_id,
                MembreCollection.utilisateur_id == user_id
            )
        )
        
        if collection_id:
            comments_query = comments_query.filter(
                CommentaireArticle.collection_id == collection_id
            )
        
        recent_comments = comments_query.order_by(
            CommentaireArticle.cree_le.desc()
        ).limit(limit // 2).all()
        
        for comment in recent_comments:
            activities.append({
                "type": "comment",
                "id": comment.id,
                "contenu": comment.contenu[:100] + "..." if len(comment.contenu) > 100 else comment.contenu,
                "utilisateur": comment.nom_utilisateur,
                "collection_id": comment.collection_id,
                "article_id": comment.article_id,
                "date": comment.cree_le
            })
        
        # Récupérer les messages récents
        messages_query = self.db.query(
            MessageCollection.id,
            MessageCollection.contenu,
            MessageCollection.cree_le,
            MessageCollection.collection_id,
            Utilisateur.nom_utilisateur
        ).join(
            Utilisateur, MessageCollection.utilisateur_id == Utilisateur.id
        ).join(
            MembreCollection, and_(
                MembreCollection.collection_id == MessageCollection.collection_id,
                MembreCollection.utilisateur_id == user_id
            )
        )
        
        if collection_id:
            messages_query = messages_query.filter(
                MessageCollection.collection_id == collection_id
            )
        
        recent_messages = messages_query.order_by(
            MessageCollection.cree_le.desc()
        ).limit(limit // 2).all()
        
        for message in recent_messages:
            activities.append({
                "type": "message",
                "id": message.id,
                "contenu": message.contenu[:100] + "..." if len(message.contenu) > 100 else message.contenu,
                "utilisateur": message.nom_utilisateur,
                "collection_id": message.collection_id,
                "date": message.cree_le
            })
        
        # Trier par date et limiter
        activities.sort(key=lambda x: x["date"], reverse=True)
        return activities[:limit]