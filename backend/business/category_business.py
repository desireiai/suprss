# business/category_business.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

# Imports corrigés pour correspondre à votre structure
from models import Categorie, FluxCategorie
from dtos.category_dto import CategoryCreateDTO, CategoryUpdateDTO, CategoryResponseDTO

logger = logging.getLogger(__name__)

class CategoryBusiness:
    """Logique métier pour la gestion des catégories"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_category(self, user_id: int, category_data: CategoryCreateDTO) -> CategoryResponseDTO:
        """Créer une nouvelle catégorie pour un utilisateur"""
        try:
            # Créer la catégorie
            categorie = Categorie(
                nom=category_data.nom,
                utilisateur_id=user_id,
                couleur=category_data.couleur,
                cree_le=datetime.utcnow()
            )
            
            self.db.add(categorie)
            self.db.commit()
            self.db.refresh(categorie)
            
            return CategoryResponseDTO(
                id=categorie.id,
                nom=categorie.nom,
                couleur=categorie.couleur,
                nombre_flux=0,
                cree_le=categorie.cree_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de la catégorie: {e}")
            raise
    
    def category_name_exists(self, user_id: int, nom: str, exclude_id: Optional[int] = None) -> bool:
        """Vérifier si une catégorie avec ce nom existe déjà pour l'utilisateur"""
        query = self.db.query(Categorie).filter(
            Categorie.utilisateur_id == user_id,
            Categorie.nom == nom
        )
        
        if exclude_id:
            query = query.filter(Categorie.id != exclude_id)
        
        return query.first() is not None
    
    def get_user_categories(self, user_id: int) -> List[CategoryResponseDTO]:
        """Obtenir toutes les catégories d'un utilisateur"""
        categories = self.db.query(Categorie).filter(
            Categorie.utilisateur_id == user_id
        ).order_by(Categorie.nom).all()
        
        results = []
        for cat in categories:
            # Compter les flux dans cette catégorie
            flux_count = self.db.query(func.count(FluxCategorie.id)).filter(
                FluxCategorie.categorie_id == cat.id
            ).scalar() or 0
            
            results.append(CategoryResponseDTO(
                id=cat.id,
                nom=cat.nom,
                couleur=cat.couleur,
                nombre_flux=flux_count,
                cree_le=cat.cree_le
            ))
        
        return results
    
    def get_category_flux_count(self, user_id: int, category_id: int) -> int:
        """Obtenir le nombre de flux dans une catégorie"""
        return self.db.query(func.count(FluxCategorie.id)).filter(
            FluxCategorie.categorie_id == category_id
        ).scalar() or 0
    
    def user_owns_category(self, user_id: int, category_id: int) -> bool:
        """Vérifier qu'une catégorie appartient à un utilisateur"""
        category = self.db.query(Categorie).filter(
            Categorie.id == category_id,
            Categorie.utilisateur_id == user_id
        ).first()
        
        return category is not None
    
    def is_default_category(self, category_id: int) -> bool:
        """Vérifier si c'est une catégorie par défaut"""
        category = self.db.query(Categorie).filter(
            Categorie.id == category_id
        ).first()
        
        return category and category.nom in ["Général", "Non classé"]
    
    def update_category(self, category_id: int, category_update: CategoryUpdateDTO) -> CategoryResponseDTO:
        """Mettre à jour une catégorie"""
        try:
            categorie = self.db.query(Categorie).filter(
                Categorie.id == category_id
            ).first()
            
            if not categorie:
                raise ValueError("Catégorie non trouvée")
            
            # Mettre à jour les champs
            if category_update.nom:
                categorie.nom = category_update.nom
            if category_update.couleur:
                categorie.couleur = category_update.couleur
            
            self.db.commit()
            self.db.refresh(categorie)
            
            # Compter les flux
            flux_count = self.db.query(func.count(FluxCategorie.id)).filter(
                FluxCategorie.categorie_id == categorie.id
            ).scalar() or 0
            
            return CategoryResponseDTO(
                id=categorie.id,
                nom=categorie.nom,
                couleur=categorie.couleur,
                nombre_flux=flux_count,
                cree_le=categorie.cree_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la catégorie: {e}")
            raise
    
    def delete_category(self, category_id: int, move_to_category_id: Optional[int] = None, user_id: int = None):
        """Supprimer une catégorie et déplacer ses flux"""
        try:
            # Trouver la catégorie à supprimer
            categorie = self.db.query(Categorie).filter(
                Categorie.id == category_id
            ).first()
            
            if not categorie:
                raise ValueError("Catégorie non trouvée")
            
            # Déterminer la catégorie de destination
            if move_to_category_id:
                dest_category = self.db.query(Categorie).filter(
                    Categorie.id == move_to_category_id
                ).first()
                if not dest_category:
                    raise ValueError("Catégorie de destination non trouvée")
            else:
                # Utiliser la catégorie par défaut
                dest_category = self.db.query(Categorie).filter(
                    Categorie.utilisateur_id == user_id,
                    Categorie.nom == "Général"
                ).first()
                
                if not dest_category:
                    # Créer la catégorie par défaut si elle n'existe pas
                    dest_category = self.create_default_category(user_id)
            
            # Déplacer tous les flux vers la catégorie de destination
            flux_categories = self.db.query(FluxCategorie).filter(
                FluxCategorie.categorie_id == category_id
            ).all()
            
            for fc in flux_categories:
                # Vérifier si le flux n'existe pas déjà dans la catégorie de destination
                existing = self.db.query(FluxCategorie).filter(
                    FluxCategorie.flux_id == fc.flux_id,
                    FluxCategorie.categorie_id == dest_category.id
                ).first()
                
                if existing:
                    # Supprimer l'ancienne association
                    self.db.delete(fc)
                else:
                    # Déplacer vers la nouvelle catégorie
                    fc.categorie_id = dest_category.id
            
            # Supprimer la catégorie
            self.db.delete(categorie)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de la catégorie: {e}")
            raise
    
    def move_flux_to_category(self, flux_id: int, from_category_id: Optional[int], to_category_id: int):
        """Déplacer un flux d'une catégorie à une autre"""
        try:
            if from_category_id:
                # Trouver l'association existante
                flux_cat = self.db.query(FluxCategorie).filter(
                    FluxCategorie.flux_id == flux_id,
                    FluxCategorie.categorie_id == from_category_id
                ).first()
                
                if flux_cat:
                    # Vérifier si le flux n'existe pas déjà dans la catégorie de destination
                    existing = self.db.query(FluxCategorie).filter(
                        FluxCategorie.flux_id == flux_id,
                        FluxCategorie.categorie_id == to_category_id
                    ).first()
                    
                    if existing:
                        # Supprimer l'ancienne association
                        self.db.delete(flux_cat)
                    else:
                        # Déplacer vers la nouvelle catégorie
                        flux_cat.categorie_id = to_category_id
            else:
                # Créer une nouvelle association
                flux_cat = FluxCategorie(
                    flux_id=flux_id,
                    categorie_id=to_category_id
                )
                self.db.add(flux_cat)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du déplacement du flux: {e}")
            raise
    
    def create_default_category(self, user_id: int) -> CategoryResponseDTO:
        """Créer la catégorie par défaut pour un utilisateur"""
        try:
            # Vérifier si elle n'existe pas déjà
            existing = self.db.query(Categorie).filter(
                Categorie.utilisateur_id == user_id,
                Categorie.nom == "Général"
            ).first()
            
            if existing:
                return CategoryResponseDTO(
                    id=existing.id,
                    nom=existing.nom,
                    couleur=existing.couleur,
                    nombre_flux=0,
                    cree_le=existing.cree_le
                )
            
            # Créer la catégorie par défaut
            categorie = Categorie(
                nom="Général",
                utilisateur_id=user_id,
                couleur="#007bff",
                cree_le=datetime.utcnow()
            )
            
            self.db.add(categorie)
            self.db.commit()
            self.db.refresh(categorie)
            
            return CategoryResponseDTO(
                id=categorie.id,
                nom=categorie.nom,
                couleur=categorie.couleur,
                nombre_flux=0,
                cree_le=categorie.cree_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de la catégorie par défaut: {e}")
            raise
    
    def get_user_default_category(self, user_id: int) -> Optional[CategoryResponseDTO]:
        """Récupérer la catégorie par défaut d'un utilisateur"""
        category = self.db.query(Categorie).filter(
            Categorie.utilisateur_id == user_id,
            Categorie.nom == "Général"
        ).first()
        
        if category:
            flux_count = self.db.query(func.count(FluxCategorie.id)).filter(
                FluxCategorie.categorie_id == category.id
            ).scalar() or 0
            
            return CategoryResponseDTO(
                id=category.id,
                nom=category.nom,
                couleur=category.couleur,
                nombre_flux=flux_count,
                cree_le=category.cree_le
            )
        
        return None