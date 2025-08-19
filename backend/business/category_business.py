# business/category_business.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.category import Categorie, FluxCategorie
from typing import Dict, Any

class CategoryBusiness:
    """Logique métier pour la gestion des catégories"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_category(self, 
                       user_id: int,
                       nom: str,
                       couleur: Optional[str] = '#007bff') -> Categorie:
        """Créer une nouvelle catégorie pour un utilisateur"""
        
        if not nom or len(nom) > 100:
            raise ValueError("Le nom de la catégorie doit faire entre 1 et 100 caractères")
        
        # Vérifier l'unicité pour cet utilisateur
        existing = self.db.query(Categorie).filter_by(
            utilisateur_id=user_id,
            nom=nom
        ).first()
        
        if existing:
            raise ValueError("Vous avez déjà une catégorie avec ce nom")
        
        # Valider la couleur (format hexadécimal)
        if couleur and not self._validate_color(couleur):
            raise ValueError("Format de couleur invalide (utilisez #RRGGBB)")
        
        categorie = Categorie(
            nom=nom,
            utilisateur_id=user_id,
            couleur=couleur
        )
        
        self.db.add(categorie)
        self.db.commit()
        
        return categorie
    
    def update_category(self, 
                       user_id: int,
                       category_id: int,
                       nom: Optional[str] = None,
                       couleur: Optional[str] = None) -> Categorie:
        """Mettre à jour une catégorie"""
        
        categorie = self.db.query(Categorie).filter_by(
            id=category_id,
            utilisateur_id=user_id
        ).first()
        
        if not categorie:
            raise ValueError("Catégorie introuvable")
        
        if nom:
            if len(nom) > 100:
                raise ValueError("Le nom doit faire moins de 100 caractères")
            
            # Vérifier l'unicité
            existing = self.db.query(Categorie).filter_by(
                utilisateur_id=user_id,
                nom=nom
            ).filter(Categorie.id != category_id).first()
            
            if existing:
                raise ValueError("Vous avez déjà une catégorie avec ce nom")
            
            categorie.nom = nom
        
        if couleur:
            if not self._validate_color(couleur):
                raise ValueError("Format de couleur invalide")
            categorie.couleur = couleur
        
        self.db.commit()
        return categorie
    
    def delete_category(self, user_id: int, category_id: int) -> bool:
        """Supprimer une catégorie (les flux seront déplacés vers Non classé)"""
        
        categorie = self.db.query(Categorie).filter_by(
            id=category_id,
            utilisateur_id=user_id
        ).first()
        
        if not categorie:
            return False
        
        # Ne pas supprimer la catégorie par défaut
        if categorie.nom == "Non classé":
            raise ValueError("Impossible de supprimer la catégorie par défaut")
        
        # Obtenir la catégorie par défaut
        default_category = self.db.query(Categorie).filter_by(
            utilisateur_id=user_id,
            nom="Non classé"
        ).first()
        
        if default_category:
            # Déplacer tous les flux vers la catégorie par défaut
            flux_categories = self.db.query(FluxCategorie).filter_by(
                categorie_id=category_id
            ).all()
            
            for fc in flux_categories:
                # Vérifier si le flux n'est pas déjà dans la catégorie par défaut
                existing = self.db.query(FluxCategorie).filter_by(
                    flux_id=fc.flux_id,
                    categorie_id=default_category.id
                ).first()
                
                if not existing:
                    fc.categorie_id = default_category.id
                else:
                    self.db.delete(fc)
        
        self.db.delete(categorie)
        self.db.commit()
        
        return True
    
    def move_flux_to_category(self, 
                             user_id: int,
                             flux_id: int,
                             from_category_id: int,
                             to_category_id: int) -> bool:
        """Déplacer un flux d'une catégorie à une autre"""
        
        # Vérifier que les deux catégories appartiennent à l'utilisateur
        from_cat = self.db.query(Categorie).filter_by(
            id=from_category_id,
            utilisateur_id=user_id
        ).first()
        
        to_cat = self.db.query(Categorie).filter_by(
            id=to_category_id,
            utilisateur_id=user_id
        ).first()
        
        if not from_cat or not to_cat:
            raise ValueError("Catégorie invalide")
        
        # Trouver l'association actuelle
        flux_cat = self.db.query(FluxCategorie).filter_by(
            flux_id=flux_id,
            categorie_id=from_category_id
        ).first()
        
        if not flux_cat:
            return False
        
        # Vérifier que le flux n'est pas déjà dans la catégorie cible
        existing = self.db.query(FluxCategorie).filter_by(
            flux_id=flux_id,
            categorie_id=to_category_id
        ).first()
        
        if existing:
            # Supprimer l'ancienne association
            self.db.delete(flux_cat)
        else:
            # Déplacer vers la nouvelle catégorie
            flux_cat.categorie_id = to_category_id
        
        self.db.commit()
        return True
    
    def get_user_categories(self, user_id: int) -> List[Dict[str, Any]]:
        """Obtenir toutes les catégories d'un utilisateur avec statistiques"""
        
        categories = self.db.query(Categorie).filter_by(
            utilisateur_id=user_id
        ).order_by(Categorie.nom).all()
        
        result = []
        for cat in categories:
            flux_count = len(cat.flux_categorie)
            
            result.append({
                'id': cat.id,
                'nom': cat.nom,
                'couleur': cat.couleur,
                'nombre_flux': flux_count,
                'cree_le': cat.cree_le
            })
        
        return result
    
    def _validate_color(self, color: str) -> bool:
        """Valider le format de couleur hexadécimal"""
        import re
        pattern = r'^#[0-9A-Fa-f]{6}$'
        return bool(re.match(pattern, color))