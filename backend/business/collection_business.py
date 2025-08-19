# business/collection_business.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.collection import Collection, CollectionFlux, MembreCollection
from ..models.rss import FluxRss
from ..models.user import Utilisateur
from ..models.interaction import CommentaireArticle, MessageCollection

class CollectionBusiness:
    """Logique métier pour la gestion des collections"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_collection(self, 
                         proprietaire_id: int,
                         nom: str,
                         description: Optional[str] = None,
                         est_partagee: bool = False) -> Collection:
        """Créer une nouvelle collection"""
        
        if not nom or len(nom) > 255:
            raise ValueError("Le nom de la collection doit faire entre 1 et 255 caractères")
        
        collection = Collection(
            nom=nom,
            proprietaire_id=proprietaire_id,
            description=description,
            est_partagee=est_partagee
        )
        
        self.db.add(collection)
        self.db.flush()
        
        # Ajouter le propriétaire comme membre avec tous les droits
        membre = MembreCollection(
            collection_id=collection.id,
            utilisateur_id=proprietaire_id,
            role='proprietaire',
            peut_ajouter_flux=True,
            peut_lire=True,
            peut_commenter=True,
            peut_modifier=True,
            peut_supprimer=True
        )
        
        self.db.add(membre)
        self.db.commit()
        self.db.refresh(collection)
        
        return collection
    
    def add_flux_to_collection(self, 
                              collection_id: int,
                              flux_id: int,
                              user_id: int) -> CollectionFlux:
        """Ajouter un flux à une collection"""
        
        # Vérifier les permissions
        if not self._can_add_flux(user_id, collection_id):
            raise PermissionError("Vous n'avez pas la permission d'ajouter des flux à cette collection")
        
        # Vérifier que le flux existe
        flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
        if not flux:
            raise ValueError("Flux introuvable")
        
        # Vérifier que l'association n'existe pas déjà
        existing = self.db.query(CollectionFlux).filter_by(
            collection_id=collection_id,
            flux_id=flux_id
        ).first()
        
        if existing:
            raise ValueError("Ce flux est déjà dans la collection")
        
        collection_flux = CollectionFlux(
            collection_id=collection_id,
            flux_id=flux_id,
            ajoute_par_utilisateur_id=user_id
        )
        
        self.db.add(collection_flux)
        self.db.commit()
        
        return collection_flux
    
    def add_member(self, 
                  collection_id: int,
                  user_id: int,
                  added_by_user_id: int,
                  role: str = 'membre',
                  permissions: Optional[Dict[str, bool]] = None) -> MembreCollection:
        """Ajouter un membre à une collection"""
        
        # Vérifier que l'utilisateur qui ajoute a les permissions
        if not self._can_modify(added_by_user_id, collection_id):
            raise PermissionError("Vous n'avez pas la permission de gérer les membres de cette collection")
        
        # Vérifier que l'utilisateur à ajouter existe
        user = self.db.query(Utilisateur).filter_by(id=user_id).first()
        if not user:
            raise ValueError("Utilisateur introuvable")
        
        # Vérifier que l'utilisateur n'est pas déjà membre
        existing = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        
        if existing:
            raise ValueError("Cet utilisateur est déjà membre de la collection")
        
        # Définir les permissions par défaut selon le rôle
        default_permissions = self._get_default_permissions(role)
        if permissions:
            default_permissions.update(permissions)
        
        membre = MembreCollection(
            collection_id=collection_id,
            utilisateur_id=user_id,
            role=role,
            **default_permissions
        )
        
        self.db.add(membre)
        self.db.commit()
        
        return membre
    
    def update_member_permissions(self,
                                 collection_id: int,
                                 member_user_id: int,
                                 updated_by_user_id: int,
                                 role: Optional[str] = None,
                                 permissions: Optional[Dict[str, bool]] = None) -> MembreCollection:
        """Mettre à jour les permissions d'un membre"""
        
        # Vérifier les permissions
        if not self._can_modify(updated_by_user_id, collection_id):
            raise PermissionError("Vous n'avez pas la permission de modifier les membres")
        
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=member_user_id
        ).first()
        
        if not membre:
            raise ValueError("Membre introuvable")
        
        # On ne peut pas modifier le propriétaire
        if membre.role == 'proprietaire' and membre.utilisateur_id != updated_by_user_id:
            raise PermissionError("Impossible de modifier les permissions du propriétaire")
        
        if role:
            membre.role = role
            # Appliquer les permissions par défaut du nouveau rôle
            default_perms = self._get_default_permissions(role)
            for key, value in default_perms.items():
                setattr(membre, key, value)
        
        if permissions:
            for key, value in permissions.items():
                if hasattr(membre, key):
                    setattr(membre, key, value)
        
        self.db.commit()
        return membre
    
    def remove_member(self, collection_id: int, member_user_id: int, removed_by_user_id: int) -> bool:
        """Retirer un membre d'une collection"""
        
        # Vérifier les permissions
        if not self._can_modify(removed_by_user_id, collection_id):
            raise PermissionError("Vous n'avez pas la permission de retirer des membres")
        
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=member_user_id
        ).first()
        
        if not membre:
            return False
        
        # On ne peut pas retirer le propriétaire
        if membre.role == 'proprietaire':
            raise PermissionError("Impossible de retirer le propriétaire de la collection")
        
        self.db.delete(membre)
        self.db.commit()
        
        return True
    
    def post_comment(self, 
                    collection_id: int,
                    article_id: int,
                    user_id: int,
                    contenu: str,
                    parent_id: Optional[int] = None) -> CommentaireArticle:
        """Poster un commentaire sur un article dans une collection"""
        
        # Vérifier les permissions
        if not self._can_comment(user_id, collection_id):
            raise PermissionError("Vous n'avez pas la permission de commenter")
        
        if not contenu or len(contenu) > 5000:
            raise ValueError("Le commentaire doit faire entre 1 et 5000 caractères")
        
        commentaire = CommentaireArticle(
            article_id=article_id,
            utilisateur_id=user_id,
            collection_id=collection_id,
            contenu=contenu,
            commentaire_parent_id=parent_id
        )
        
        self.db.add(commentaire)
        self.db.commit()
        
        return commentaire
    
    def post_message(self, 
                    collection_id: int,
                    user_id: int,
                    contenu: str) -> MessageCollection:
        """Poster un message dans le chat de la collection"""
        
        # Vérifier les permissions
        if not self._can_comment(user_id, collection_id):
            raise PermissionError("Vous n'avez pas la permission d'envoyer des messages")
        
        if not contenu or len(contenu) > 2000:
            raise ValueError("Le message doit faire entre 1 et 2000 caractères")
        
        message = MessageCollection(
            collection_id=collection_id,
            utilisateur_id=user_id,
            contenu=contenu
        )
        
        self.db.add(message)
        self.db.commit()
        
        return message
    
    def get_user_collections(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtenir toutes les collections d'un utilisateur"""
        
        # Collections où l'utilisateur est membre
        memberships = self.db.query(MembreCollection).filter_by(
            utilisateur_id=user_id
        ).all()
        
        collections = []
        for membership in memberships:
            collection = membership.collection
            
            # Compter les flux et membres
            flux_count = self.db.query(CollectionFlux).filter_by(
                collection_id=collection.id
            ).count()
            
            member_count = self.db.query(MembreCollection).filter_by(
                collection_id=collection.id
            ).count()
            
            collections.append({
                'id': collection.id,
                'nom': collection.nom,
                'description': collection.description,
                'est_partagee': collection.est_partagee,
                'proprietaire': collection.proprietaire.nom_utilisateur,
                'mon_role': membership.role,
                'nombre_flux': flux_count,
                'nombre_membres': member_count,
                'cree_le': collection.cree_le,
                'permissions': {
                    'peut_ajouter_flux': membership.peut_ajouter_flux,
                    'peut_lire': membership.peut_lire,
                    'peut_commenter': membership.peut_commenter,
                    'peut_modifier': membership.peut_modifier,
                    'peut_supprimer': membership.peut_supprimer
                }
            })
        
        return collections
    
    def get_collection_details(self, collection_id: int, user_id: int) -> Dict[str, Any]:
        """Obtenir les détails d'une collection"""
        
        # Vérifier que l'utilisateur peut lire la collection
        if not self._can_read(user_id, collection_id):
            raise PermissionError("Vous n'avez pas accès à cette collection")
        
        collection = self.db.query(Collection).filter_by(id=collection_id).first()
        
        if not collection:
            raise ValueError("Collection introuvable")
        
        # Obtenir les flux
        flux_list = []
        for cf in collection.collection_flux:
            flux_list.append({
                'id': cf.flux.id,
                'nom': cf.flux.nom,
                'url': cf.flux.url,
                'description': cf.flux.description,
                'ajoute_par': cf.ajoute_par_utilisateur.nom_utilisateur,
                'ajoute_le': cf.ajoute_le
            })
        
        # Obtenir les membres
        membres_list = []
        for membre in collection.membre_collection:
            membres_list.append({
                'id': membre.utilisateur.id,
                'nom_utilisateur': membre.utilisateur.nom_utilisateur,
                'email': membre.utilisateur.email,
                'role': membre.role,
                'rejoint_le': membre.rejoint_le,
                'permissions': {
                    'peut_ajouter_flux': membre.peut_ajouter_flux,
                    'peut_lire': membre.peut_lire,
                    'peut_commenter': membre.peut_commenter,
                    'peut_modifier': membre.peut_modifier,
                    'peut_supprimer': membre.peut_supprimer
                }
            })
        
        return {
            'id': collection.id,
            'nom': collection.nom,
            'description': collection.description,
            'est_partagee': collection.est_partagee,
            'proprietaire': {
                'id': collection.proprietaire.id,
                'nom_utilisateur': collection.proprietaire.nom_utilisateur
            },
            'flux': flux_list,
            'membres': membres_list,
            'cree_le': collection.cree_le,
            'modifie_le': collection.modifie_le
        }
    
    def delete_collection(self, collection_id: int, user_id: int) -> bool:
        """Supprimer une collection"""
        
        # Seul le propriétaire peut supprimer
        collection = self.db.query(Collection).filter_by(
            id=collection_id,
            proprietaire_id=user_id
        ).first()
        
        if not collection:
            raise PermissionError("Vous ne pouvez supprimer que vos propres collections")
        
        self.db.delete(collection)
        self.db.commit()
        
        return True
    
    # Méthodes privées pour vérifier les permissions
    def _can_read(self, user_id: int, collection_id: int) -> bool:
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        return membre and membre.peut_lire
    
    def _can_add_flux(self, user_id: int, collection_id: int) -> bool:
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        return membre and membre.peut_ajouter_flux
    
    def _can_comment(self, user_id: int, collection_id: int) -> bool:
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        return membre and membre.peut_commenter
    
    def _can_modify(self, user_id: int, collection_id: int) -> bool:
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        return membre and membre.peut_modifier
    
    def _can_delete(self, user_id: int, collection_id: int) -> bool:
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        return membre and membre.peut_supprimer
    
    def _get_default_permissions(self, role: str) -> Dict[str, bool]:
        """Obtenir les permissions par défaut selon le rôle"""
        if role == 'proprietaire':
            return {
                'peut_ajouter_flux': True,
                'peut_lire': True,
                'peut_commenter': True,
                'peut_modifier': True,
                'peut_supprimer': True
            }
        elif role == 'administrateur':
            return {
                'peut_ajouter_flux': True,
                'peut_lire': True,
                'peut_commenter': True,
                'peut_modifier': True,
                'peut_supprimer': False
            }
        elif role == 'moderateur':
            return {
                'peut_ajouter_flux': True,
                'peut_lire': True,
                'peut_commenter': True,
                'peut_modifier': False,
                'peut_supprimer': False
            }
        else:  # membre
            return {
                'peut_ajouter_flux': True,
                'peut_lire': True,
                'peut_commenter': True,
                'peut_modifier': False,
                'peut_supprimer': False
            }
