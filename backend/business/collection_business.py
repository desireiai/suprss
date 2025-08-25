# business/collection_business.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

# Imports corrigés pour correspondre à votre structure
from models import (
    Collection, 
    CollectionFlux, 
    MembreCollection,
    FluxRss,
    Utilisateur,
    CommentaireArticle, 
    MessageCollection
)
from dtos.collection_dto import (
    CollectionCreateDTO,
    CollectionUpdateDTO,
    CollectionResponseDTO,
    CollectionDetailResponseDTO,
    CollectionMemberAddDTO,
    CollectionMemberUpdateDTO,
    CollectionMemberResponseDTO,
    CollectionFluxResponseDTO
)

logger = logging.getLogger(__name__)

class CollectionBusiness:
    """Logique métier pour la gestion des collections"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_collection(self, user_id: int, collection_data: CollectionCreateDTO) -> CollectionResponseDTO:
        """Créer une nouvelle collection"""
        try:
            collection = Collection(
                nom=collection_data.nom,
                proprietaire_id=user_id,
                description=collection_data.description,
                est_partagee=collection_data.est_partagee,
                cree_le=datetime.utcnow(),
                modifie_le=datetime.utcnow()
            )
            
            self.db.add(collection)
            self.db.flush()
            
            # Ajouter le propriétaire comme membre avec tous les droits
            membre = MembreCollection(
                collection_id=collection.id,
                utilisateur_id=user_id,
                role='proprietaire',
                peut_ajouter_flux=True,
                peut_lire=True,
                peut_commenter=True,
                peut_modifier=True,
                peut_supprimer=True,
                rejoint_le=datetime.utcnow()
            )
            
            self.db.add(membre)
            self.db.commit()
            self.db.refresh(collection)
            
            # Récupérer le nom du propriétaire
            proprietaire_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == user_id
            ).scalar() or "Utilisateur inconnu"
            
            return CollectionResponseDTO(
                id=collection.id,
                nom=collection.nom,
                description=collection.description,
                est_partagee=collection.est_partagee,
                proprietaire_id=collection.proprietaire_id,
                proprietaire_nom=proprietaire_nom,
                nombre_flux=0,
                nombre_membres=1,
                mon_role="proprietaire",
                mes_permissions={
                    "peut_ajouter_flux": True,
                    "peut_lire": True,
                    "peut_commenter": True,
                    "peut_modifier": True,
                    "peut_supprimer": True
                },
                cree_le=collection.cree_le,
                modifie_le=collection.modifie_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de la collection: {e}")
            raise
    
    def get_user_collections(
        self, 
        user_id: int,
        include_shared: bool = True,
        only_owned: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[CollectionResponseDTO], int]:
        """Obtenir les collections d'un utilisateur avec pagination"""
        
        # Requête de base pour les collections accessibles
        query = self.db.query(Collection).join(
            MembreCollection
        ).filter(
            MembreCollection.utilisateur_id == user_id
        )
        
        if only_owned:
            query = query.filter(Collection.proprietaire_id == user_id)
        elif not include_shared:
            query = query.filter(Collection.est_partagee == False)
        
        # Total pour la pagination
        total = query.count()
        
        # Appliquer la pagination
        offset = (page - 1) * page_size
        collections = query.offset(offset).limit(page_size).all()
        
        # Convertir en DTOs
        results = []
        for collection in collections:
            # Compter flux et membres
            nombre_flux = self.db.query(func.count(CollectionFlux.id)).filter(
                CollectionFlux.collection_id == collection.id
            ).scalar() or 0
            
            nombre_membres = self.db.query(func.count(MembreCollection.id)).filter(
                MembreCollection.collection_id == collection.id
            ).scalar() or 0
            
            # Récupérer le nom du propriétaire
            proprietaire_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == collection.proprietaire_id
            ).scalar() or "Utilisateur inconnu"
            
            results.append(CollectionResponseDTO(
                id=collection.id,
                nom=collection.nom,
                description=collection.description,
                est_partagee=collection.est_partagee,
                proprietaire_id=collection.proprietaire_id,
                proprietaire_nom=proprietaire_nom,
                nombre_flux=nombre_flux,
                nombre_membres=nombre_membres,
                cree_le=collection.cree_le,
                modifie_le=collection.modifie_le
            ))
        
        return results, total
    
    def get_collection_detail(self, collection_id: int) -> Optional[CollectionDetailResponseDTO]:
        """Récupérer les détails d'une collection"""
        collection = self.db.query(Collection).filter(
            Collection.id == collection_id
        ).first()
        
        if not collection:
            return None
        
        # Récupérer les flux
        flux_query = self.db.query(
            FluxRss.id,
            FluxRss.nom,
            FluxRss.url,
            FluxRss.description,
            Utilisateur.nom_utilisateur.label('ajoute_par'),
            CollectionFlux.ajoute_le
        ).join(
            CollectionFlux, FluxRss.id == CollectionFlux.flux_id
        ).join(
            Utilisateur, CollectionFlux.ajoute_par_utilisateur_id == Utilisateur.id
        ).filter(
            CollectionFlux.collection_id == collection_id
        ).all()
        
        flux_list = [
            CollectionFluxResponseDTO(
                id=f.id,
                nom=f.nom,
                url=f.url,
                description=f.description,
                ajoute_par=f.ajoute_par,
                ajoute_le=f.ajoute_le
            ) for f in flux_query
        ]
        
        # Récupérer les membres
        membres_query = self.db.query(
            Utilisateur.id,
            Utilisateur.nom_utilisateur,
            Utilisateur.email,
            MembreCollection.role,
            MembreCollection.rejoint_le,
            MembreCollection.peut_ajouter_flux,
            MembreCollection.peut_lire,
            MembreCollection.peut_commenter,
            MembreCollection.peut_modifier,
            MembreCollection.peut_supprimer
        ).join(
            MembreCollection, Utilisateur.id == MembreCollection.utilisateur_id
        ).filter(
            MembreCollection.collection_id == collection_id
        ).all()
        
        membres_list = [
            CollectionMemberResponseDTO(
                id=m.id,
                nom_utilisateur=m.nom_utilisateur,
                email=m.email,
                role=m.role,
                rejoint_le=m.rejoint_le,
                permissions={
                    "peut_ajouter_flux": m.peut_ajouter_flux,
                    "peut_lire": m.peut_lire,
                    "peut_commenter": m.peut_commenter,
                    "peut_modifier": m.peut_modifier,
                    "peut_supprimer": m.peut_supprimer
                }
            ) for m in membres_query
        ]
        
        # Récupérer le nom du propriétaire
        proprietaire_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
            Utilisateur.id == collection.proprietaire_id
        ).scalar() or "Utilisateur inconnu"
        
        return CollectionDetailResponseDTO(
            id=collection.id,
            nom=collection.nom,
            description=collection.description,
            est_partagee=collection.est_partagee,
            proprietaire_id=collection.proprietaire_id,
            proprietaire_nom=proprietaire_nom,
            nombre_flux=len(flux_list),
            nombre_membres=len(membres_list),
            cree_le=collection.cree_le,
            modifie_le=collection.modifie_le,
            flux=flux_list,
            membres=membres_list
        )
    
    def user_can_read_collection(self, user_id: int, collection_id: int) -> bool:
        """Vérifier si un utilisateur peut lire une collection"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id,
            MembreCollection.peut_lire == True
        ).first()
        
        return member is not None
    
    def user_can_modify_collection(self, user_id: int, collection_id: int) -> bool:
        """Vérifier si un utilisateur peut modifier une collection"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id,
            MembreCollection.peut_modifier == True
        ).first()
        
        return member is not None
    
    def user_owns_collection(self, user_id: int, collection_id: int) -> bool:
        """Vérifier si un utilisateur est propriétaire d'une collection"""
        collection = self.db.query(Collection).filter(
            Collection.id == collection_id,
            Collection.proprietaire_id == user_id
        ).first()
        
        return collection is not None
    
    def user_can_add_flux(self, user_id: int, collection_id: int) -> bool:
        """Vérifier si un utilisateur peut ajouter des flux"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id,
            MembreCollection.peut_ajouter_flux == True
        ).first()
        
        return member is not None
    
    def user_can_delete_in_collection(self, user_id: int, collection_id: int) -> bool:
        """Vérifier si un utilisateur peut supprimer dans une collection"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id,
            MembreCollection.peut_supprimer == True
        ).first()
        
        return member is not None
    
    def get_user_role_in_collection(self, user_id: int, collection_id: int) -> Optional[str]:
        """Récupérer le rôle d'un utilisateur dans une collection"""
        member = self.db.query(MembreCollection.role).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id
        ).scalar()
        
        return member
    
    def get_user_permissions(self, user_id: int, collection_id: int) -> Optional[Dict[str, bool]]:
        """Récupérer les permissions d'un utilisateur dans une collection"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id
        ).first()
        
        if not member:
            return None
        
        return {
            "peut_ajouter_flux": member.peut_ajouter_flux,
            "peut_lire": member.peut_lire,
            "peut_commenter": member.peut_commenter,
            "peut_modifier": member.peut_modifier,
            "peut_supprimer": member.peut_supprimer
        }
    
    def update_collection(self, collection_id: int, collection_update: CollectionUpdateDTO) -> CollectionResponseDTO:
        """Mettre à jour une collection"""
        try:
            collection = self.db.query(Collection).filter(
                Collection.id == collection_id
            ).first()
            
            if not collection:
                raise ValueError("Collection non trouvée")
            
            if collection_update.nom:
                collection.nom = collection_update.nom
            if collection_update.description is not None:
                collection.description = collection_update.description
            
            collection.modifie_le = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(collection)
            
            # Compter flux et membres
            nombre_flux = self.db.query(func.count(CollectionFlux.id)).filter(
                CollectionFlux.collection_id == collection.id
            ).scalar() or 0
            
            nombre_membres = self.db.query(func.count(MembreCollection.id)).filter(
                MembreCollection.collection_id == collection.id
            ).scalar() or 0
            
            # Récupérer le nom du propriétaire
            proprietaire_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == collection.proprietaire_id
            ).scalar() or "Utilisateur inconnu"
            
            return CollectionResponseDTO(
                id=collection.id,
                nom=collection.nom,
                description=collection.description,
                est_partagee=collection.est_partagee,
                proprietaire_id=collection.proprietaire_id,
                proprietaire_nom=proprietaire_nom,
                nombre_flux=nombre_flux,
                nombre_membres=nombre_membres,
                cree_le=collection.cree_le,
                modifie_le=collection.modifie_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la collection: {e}")
            raise
    
    def delete_collection(self, collection_id: int):
        """Supprimer une collection"""
        try:
            collection = self.db.query(Collection).filter(
                Collection.id == collection_id
            ).first()
            
            if not collection:
                raise ValueError("Collection non trouvée")
            
            self.db.delete(collection)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de la collection: {e}")
            raise
    
    def add_flux_to_collection(self, collection_id: int, flux_id: int, user_id: int = None):
        """Ajouter un flux à une collection"""
        try:
            # Vérifier que l'association n'existe pas déjà
            existing = self.db.query(CollectionFlux).filter(
                CollectionFlux.collection_id == collection_id,
                CollectionFlux.flux_id == flux_id
            ).first()
            
            if existing:
                raise ValueError("Ce flux est déjà dans la collection")
            
            collection_flux = CollectionFlux(
                collection_id=collection_id,
                flux_id=flux_id,
                ajoute_par_utilisateur_id=user_id or 1,  # Fallback si user_id n'est pas fourni
                ajoute_le=datetime.utcnow()
            )
            
            self.db.add(collection_flux)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'ajout du flux à la collection: {e}")
            raise
    
    def remove_flux_from_collection(self, collection_id: int, flux_id: int):
        """Retirer un flux d'une collection"""
        try:
            collection_flux = self.db.query(CollectionFlux).filter(
                CollectionFlux.collection_id == collection_id,
                CollectionFlux.flux_id == flux_id
            ).first()
            
            if collection_flux:
                self.db.delete(collection_flux)
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression du flux: {e}")
            raise
    
    def is_user_member(self, user_id: int, collection_id: int) -> bool:
        """Vérifier si un utilisateur est membre d'une collection"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == user_id
        ).first()
        
        return member is not None
    
    def add_member_to_collection(self, collection_id: int, member_data: CollectionMemberAddDTO) -> CollectionMemberResponseDTO:
        """Ajouter un membre à une collection"""
        try:
            # Permissions par défaut selon le rôle
            permissions = self._get_default_permissions(member_data.role.value)
            
            if member_data.permissions_custom:
                permissions.update(member_data.permissions_custom)
            
            membre = MembreCollection(
                collection_id=collection_id,
                utilisateur_id=member_data.utilisateur_id,
                role=member_data.role.value,
                peut_ajouter_flux=permissions.get('peut_ajouter_flux', True),
                peut_lire=permissions.get('peut_lire', True),
                peut_commenter=permissions.get('peut_commenter', True),
                peut_modifier=permissions.get('peut_modifier', False),
                peut_supprimer=permissions.get('peut_supprimer', False),
                rejoint_le=datetime.utcnow()
            )
            
            self.db.add(membre)
            self.db.commit()
            self.db.refresh(membre)
            
            # Récupérer les infos utilisateur
            user_info = self.db.query(
                Utilisateur.nom_utilisateur,
                Utilisateur.email
            ).filter(
                Utilisateur.id == member_data.utilisateur_id
            ).first()
            
            return CollectionMemberResponseDTO(
                id=membre.utilisateur_id,
                nom_utilisateur=user_info.nom_utilisateur,
                email=user_info.email,
                role=membre.role,
                rejoint_le=membre.rejoint_le,
                permissions={
                    "peut_ajouter_flux": membre.peut_ajouter_flux,
                    "peut_lire": membre.peut_lire,
                    "peut_commenter": membre.peut_commenter,
                    "peut_modifier": membre.peut_modifier,
                    "peut_supprimer": membre.peut_supprimer
                }
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'ajout du membre: {e}")
            raise
    
    def update_member_permissions(self, collection_id: int, member_id: int, member_update: CollectionMemberUpdateDTO) -> CollectionMemberResponseDTO:
        """Mettre à jour les permissions d'un membre"""
        try:
            membre = self.db.query(MembreCollection).filter(
                MembreCollection.collection_id == collection_id,
                MembreCollection.utilisateur_id == member_id
            ).first()
            
            if not membre:
                raise ValueError("Membre non trouvé")
            
            # Mettre à jour les champs
            if member_update.role:
                membre.role = member_update.role.value
                # Appliquer les permissions par défaut du nouveau rôle
                default_perms = self._get_default_permissions(member_update.role.value)
                for key, value in default_perms.items():
                    setattr(membre, key, value)
            
            # Permissions individuelles
            if member_update.peut_ajouter_flux is not None:
                membre.peut_ajouter_flux = member_update.peut_ajouter_flux
            if member_update.peut_lire is not None:
                membre.peut_lire = member_update.peut_lire
            if member_update.peut_commenter is not None:
                membre.peut_commenter = member_update.peut_commenter
            if member_update.peut_modifier is not None:
                membre.peut_modifier = member_update.peut_modifier
            if member_update.peut_supprimer is not None:
                membre.peut_supprimer = member_update.peut_supprimer
            
            self.db.commit()
            self.db.refresh(membre)
            
            # Récupérer les infos utilisateur
            user_info = self.db.query(
                Utilisateur.nom_utilisateur,
                Utilisateur.email
            ).filter(
                Utilisateur.id == member_id
            ).first()
            
            return CollectionMemberResponseDTO(
                id=membre.utilisateur_id,
                nom_utilisateur=user_info.nom_utilisateur,
                email=user_info.email,
                role=membre.role,
                rejoint_le=membre.rejoint_le,
                permissions={
                    "peut_ajouter_flux": membre.peut_ajouter_flux,
                    "peut_lire": membre.peut_lire,
                    "peut_commenter": membre.peut_commenter,
                    "peut_modifier": membre.peut_modifier,
                    "peut_supprimer": membre.peut_supprimer
                }
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour du membre: {e}")
            raise
    
    def is_member_owner(self, member_id: int, collection_id: int) -> bool:
        """Vérifier si un membre est le propriétaire"""
        member = self.db.query(MembreCollection).filter(
            MembreCollection.collection_id == collection_id,
            MembreCollection.utilisateur_id == member_id,
            MembreCollection.role == 'proprietaire'
        ).first()
        
        return member is not None
    
    def get_member_user_id(self, member_id: int) -> Optional[int]:
        """Récupérer l'ID utilisateur d'un membre"""
        # Dans ce cas, member_id est déjà l'user_id
        return member_id
    
    def remove_member_from_collection(self, member_id: int):
        """Retirer un membre de la collection"""
        # Note: Cette méthode suppose que member_id est l'ID du membre dans la table MembreCollection
        # Si c'est l'user_id, il faut adapter
        try:
            membre = self.db.query(MembreCollection).filter(
                MembreCollection.id == member_id
            ).first()
            
            if membre:
                self.db.delete(membre)
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression du membre: {e}")
            raise
    
    def get_collection_members(self, collection_id: int) -> List[CollectionMemberResponseDTO]:
        """Récupérer la liste des membres d'une collection"""
        membres_query = self.db.query(
            MembreCollection.id,
            Utilisateur.nom_utilisateur,
            Utilisateur.email,
            MembreCollection.role,
            MembreCollection.rejoint_le,
            MembreCollection.peut_ajouter_flux,
            MembreCollection.peut_lire,
            MembreCollection.peut_commenter,
            MembreCollection.peut_modifier,
            MembreCollection.peut_supprimer
        ).join(
            Utilisateur, MembreCollection.utilisateur_id == Utilisateur.id
        ).filter(
            MembreCollection.collection_id == collection_id
        ).all()
        
        return [
            CollectionMemberResponseDTO(
                id=m.id,
                nom_utilisateur=m.nom_utilisateur,
                email=m.email,
                role=m.role,
                rejoint_le=m.rejoint_le,
                permissions={
                    "peut_ajouter_flux": m.peut_ajouter_flux,
                    "peut_lire": m.peut_lire,
                    "peut_commenter": m.peut_commenter,
                    "peut_modifier": m.peut_modifier,
                    "peut_supprimer": m.peut_supprimer
                }
            ) for m in membres_query
        ]
    
    def toggle_sharing(self, collection_id: int, is_shared: bool) -> CollectionResponseDTO:
        """Activer ou désactiver le partage d'une collection"""
        try:
            collection = self.db.query(Collection).filter(
                Collection.id == collection_id
            ).first()
            
            if not collection:
                raise ValueError("Collection non trouvée")
            
            collection.est_partagee = is_shared
            collection.modifie_le = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(collection)
            
            # Compter flux et membres
            nombre_flux = self.db.query(func.count(CollectionFlux.id)).filter(
                CollectionFlux.collection_id == collection.id
            ).scalar() or 0
            
            nombre_membres = self.db.query(func.count(MembreCollection.id)).filter(
                MembreCollection.collection_id == collection.id
            ).scalar() or 0
            
            # Récupérer le nom du propriétaire
            proprietaire_nom = self.db.query(Utilisateur.nom_utilisateur).filter(
                Utilisateur.id == collection.proprietaire_id
            ).scalar() or "Utilisateur inconnu"
            
            return CollectionResponseDTO(
                id=collection.id,
                nom=collection.nom,
                description=collection.description,
                est_partagee=collection.est_partagee,
                proprietaire_id=collection.proprietaire_id,
                proprietaire_nom=proprietaire_nom,
                nombre_flux=nombre_flux,
                nombre_membres=nombre_membres,
                cree_le=collection.cree_le,
                modifie_le=collection.modifie_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du changement de partage: {e}")
            raise
    
    def get_pending_invitations(self, collection_id: int) -> List[Dict]:
        """Récupérer les invitations en attente (stub - nécessiterait une table dédiée)"""
        # Cette fonctionnalité nécessiterait une table d'invitations séparée
        # Pour l'instant, on retourne une liste vide
        return []
    
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