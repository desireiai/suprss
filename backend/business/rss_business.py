# business/rss_business.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import feedparser
import xml.etree.ElementTree as ET
import logging
import hashlib
import time

from models.rss import FluxRss, Article
from models.category import Categorie, FluxCategorie
from models.interaction import StatutUtilisateurArticle
from models.import_export import JournalImport, JournalExport
from dtos.rss_dto import (
    FluxCreateDTO,
    FluxUpdateDTO,
    FluxResponseDTO,
    ArticleResponseDTO,
    ArticleFilterDTO
)

logger = logging.getLogger(__name__)

class RssBusiness:
    """Logique métier pour la gestion des flux RSS"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def flux_exists_for_user(self, user_id: int, url: str) -> bool:
        """Vérifie si un flux existe déjà pour un utilisateur"""
        exists = self.db.query(FluxRss).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id,
            FluxRss.url == url
        ).first()
        
        return exists is not None
    
    def create_flux(self, user_id: int, flux_data: FluxCreateDTO) -> FluxResponseDTO:
        """Crée un nouveau flux RSS pour l'utilisateur"""
        try:
            # Vérifier si le flux existe déjà globalement
            flux = self.db.query(FluxRss).filter_by(url=str(flux_data.url)).first()
            
            if not flux:
                # Parser le flux pour obtenir les informations
                feed_info = self._parse_feed_info(str(flux_data.url))
                
                # Créer le nouveau flux
                flux = FluxRss(
                    nom=flux_data.nom_personnalise or feed_info.get('title', 'Flux sans titre'),
                    url=str(flux_data.url),
                    description=feed_info.get('description', ''),
                    frequence_maj_heures=flux_data.frequence_maj_heures,
                    est_actif=True,
                    derniere_maj=datetime.utcnow()
                )
                self.db.add(flux)
                self.db.flush()
            
            # Obtenir ou créer la catégorie
            if flux_data.categorie_id:
                categorie_id = flux_data.categorie_id
            else:
                # Utiliser la catégorie par défaut "Non classé"
                categorie = self.db.query(Categorie).filter_by(
                    utilisateur_id=user_id,
                    nom="Non classé"
                ).first()
                
                if not categorie:
                    # Créer la catégorie par défaut si elle n'existe pas
                    categorie = Categorie(
                        nom="Non classé",
                        utilisateur_id=user_id,
                        couleur="#007bff"
                    )
                    self.db.add(categorie)
                    self.db.flush()
                
                categorie_id = categorie.id
            
            # Associer le flux à la catégorie de l'utilisateur
            flux_cat = FluxCategorie(
                flux_id=flux.id,
                categorie_id=categorie_id
            )
            self.db.add(flux_cat)
            
            self.db.commit()
            
            # Retourner le DTO
            return FluxResponseDTO(
                id=flux.id,
                nom=flux.nom,
                url=flux.url,
                description=flux.description,
                frequence_maj_heures=flux.frequence_maj_heures,
                est_actif=flux.est_actif,
                derniere_maj=flux.derniere_maj,
                nombre_articles=0,
                cree_le=flux.cree_le
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création du flux: {e}")
            raise
    
    def fetch_flux_articles(self, flux_id: int) -> int:
        """Récupère les articles d'un flux RSS"""
        try:
            flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
            if not flux:
                return 0
            
            feed = feedparser.parse(flux.url)
            new_articles = 0
            
            for entry in feed.entries:
                # Générer un GUID unique
                guid = entry.get('id', entry.get('link', ''))
                if not guid:
                    guid_content = f"{entry.get('title', '')}{entry.get('published', '')}"
                    guid = hashlib.md5(guid_content.encode()).hexdigest()
                
                guid = guid[:500]
                
                # Vérifier si l'article existe déjà
                exists = self.db.query(Article).filter_by(
                    flux_id=flux_id,
                    guid=guid
                ).first()
                
                if not exists:
                    # Parser la date
                    publie_le = None
                    if hasattr(entry, 'published_parsed'):
                        try:
                            publie_le = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        except:
                            publie_le = datetime.utcnow()
                    else:
                        publie_le = datetime.utcnow()
                    
                    # Extraire le contenu
                    contenu = None
                    if hasattr(entry, 'content'):
                        contenu = entry.content[0].get('value', '')
                    
                    article = Article(
                        flux_id=flux_id,
                        titre=entry.get('title', 'Sans titre')[:500],
                        lien=entry.get('link', ''),
                        guid=guid,
                        auteur=entry.get('author', '')[:255] if entry.get('author') else None,
                        contenu=contenu,
                        resume=entry.get('summary', ''),
                        publie_le=publie_le
                    )
                    
                    self.db.add(article)
                    new_articles += 1
            
            # Mettre à jour la date de dernière MAJ
            flux.derniere_maj = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Ajouté {new_articles} articles pour le flux {flux_id}")
            return new_articles
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la récupération des articles: {e}")
            return 0
    
    def get_user_flux(
        self,
        user_id: int,
        categorie_id: Optional[int] = None,
        est_actif: Optional[bool] = None
    ) -> List[FluxResponseDTO]:
        """Récupère les flux de l'utilisateur"""
        query = self.db.query(FluxRss).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id
        )
        
        if categorie_id:
            query = query.filter(Categorie.id == categorie_id)
        
        if est_actif is not None:
            query = query.filter(FluxRss.est_actif == est_actif)
        
        flux_list = query.all()
        
        results = []
        for flux in flux_list:
            # Compter les articles
            nombre_articles = self.db.query(Article).filter_by(flux_id=flux.id).count()
            
            results.append(FluxResponseDTO(
                id=flux.id,
                nom=flux.nom,
                url=flux.url,
                description=flux.description,
                frequence_maj_heures=flux.frequence_maj_heures,
                est_actif=flux.est_actif,
                derniere_maj=flux.derniere_maj,
                nombre_articles=nombre_articles,
                cree_le=flux.cree_le
            ))
        
        return results
    
    def get_flux_by_id(self, flux_id: int) -> Optional[FluxResponseDTO]:
        """Récupère un flux par son ID"""
        flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
        
        if not flux:
            return None
        
        nombre_articles = self.db.query(Article).filter_by(flux_id=flux.id).count()
        
        return FluxResponseDTO(
            id=flux.id,
            nom=flux.nom,
            url=flux.url,
            description=flux.description,
            frequence_maj_heures=flux.frequence_maj_heures,
            est_actif=flux.est_actif,
            derniere_maj=flux.derniere_maj,
            nombre_articles=nombre_articles,
            cree_le=flux.cree_le
        )
    
    def user_owns_flux(self, user_id: int, flux_id: int) -> bool:
        """Vérifie si un utilisateur possède un flux"""
        exists = self.db.query(FluxCategorie).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id,
            FluxCategorie.flux_id == flux_id
        ).first()
        
        return exists is not None
    
    def update_flux(self, flux_id: int, flux_update: FluxUpdateDTO) -> FluxResponseDTO:
        """Met à jour un flux"""
        flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
        
        if not flux:
            raise ValueError("Flux non trouvé")
        
        if flux_update.nom:
            flux.nom = flux_update.nom
        if flux_update.description is not None:
            flux.description = flux_update.description
        if flux_update.frequence_maj_heures:
            flux.frequence_maj_heures = flux_update.frequence_maj_heures
        if flux_update.est_actif is not None:
            flux.est_actif = flux_update.est_actif
        
        flux.modifie_le = datetime.utcnow()
        self.db.commit()
        
        nombre_articles = self.db.query(Article).filter_by(flux_id=flux.id).count()
        
        return FluxResponseDTO(
            id=flux.id,
            nom=flux.nom,
            url=flux.url,
            description=flux.description,
            frequence_maj_heures=flux.frequence_maj_heures,
            est_actif=flux.est_actif,
            derniere_maj=flux.derniere_maj,
            nombre_articles=nombre_articles,
            cree_le=flux.cree_le
        )
    
    def delete_flux(self, flux_id: int):
        """Supprime un flux (retire l'association avec l'utilisateur)"""
        # Note: On ne supprime pas le flux lui-même, juste l'association
        # Le flux pourrait être utilisé par d'autres utilisateurs
        flux_cats = self.db.query(FluxCategorie).filter_by(flux_id=flux_id).all()
        
        for fc in flux_cats:
            self.db.delete(fc)
        
        self.db.commit()
    
    def can_refresh_flux(self, flux_id: int) -> bool:
        """Vérifie si un flux peut être rafraîchi"""
        flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
        
        if not flux or not flux.derniere_maj:
            return True
        
        # Vérifier si assez de temps s'est écoulé depuis la dernière MAJ
        delta = datetime.utcnow() - flux.derniere_maj
        min_interval = timedelta(minutes=5)  # Minimum 5 minutes entre les MAJ
        
        return delta >= min_interval
    
    def get_user_articles(
        self,
        user_id: int,
        filters: ArticleFilterDTO,
        sort_by: Optional[str] = None,
        sort_order: str = "desc"
    ) -> Tuple[List[ArticleResponseDTO], int]:
        """Récupère les articles de l'utilisateur avec filtres"""
        # Requête de base
        query = self.db.query(Article).join(
            FluxRss
        ).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id
        )
        
        # Appliquer les filtres
        if filters.categorie_id:
            query = query.filter(Categorie.id == filters.categorie_id)
        
        if filters.flux_id:
            query = query.filter(FluxRss.id == filters.flux_id)
        
        if filters.search_query:
            pattern = f"%{filters.search_query}%"
            query = query.filter(
                or_(
                    Article.titre.ilike(pattern),
                    Article.contenu.ilike(pattern),
                    Article.resume.ilike(pattern)
                )
            )
        
        if filters.date_debut:
            query = query.filter(Article.publie_le >= filters.date_debut)
        
        if filters.date_fin:
            query = query.filter(Article.publie_le <= filters.date_fin)
        
        # Joindre les statuts utilisateur
        query = query.outerjoin(
            StatutUtilisateurArticle,
            and_(
                StatutUtilisateurArticle.article_id == Article.id,
                StatutUtilisateurArticle.utilisateur_id == user_id
            )
        )
        
        # Filtrer par statut
        if filters.only_unread:
            query = query.filter(
                or_(
                    StatutUtilisateurArticle.est_lu == False,
                    StatutUtilisateurArticle.est_lu.is_(None)
                )
            )
        
        if filters.only_favorites:
            query = query.filter(StatutUtilisateurArticle.est_favori == True)
        
        # Compter avant pagination
        total = query.count()
        
        # Tri
        if sort_by == "date":
            if sort_order == "asc":
                query = query.order_by(Article.publie_le.asc())
            else:
                query = query.order_by(Article.publie_le.desc())
        elif sort_by == "title":
            if sort_order == "asc":
                query = query.order_by(Article.titre.asc())
            else:
                query = query.order_by(Article.titre.desc())
        else:
            query = query.order_by(Article.publie_le.desc())
        
        # Pagination
        articles = query.offset(filters.offset).limit(filters.limit).all()
        
        # Convertir en DTOs
        results = []
        for article in articles:
            statut = self.db.query(StatutUtilisateurArticle).filter_by(
                utilisateur_id=user_id,
                article_id=article.id
            ).first()
            
            results.append(ArticleResponseDTO(
                id=article.id,
                titre=article.titre,
                lien=article.lien,
                auteur=article.auteur,
                resume=article.resume,
                contenu=article.contenu,
                publie_le=article.publie_le,
                flux_id=article.flux_id,
                flux_nom=article.flux.nom,
                est_lu=statut.est_lu if statut else False,
                est_favori=statut.est_favori if statut else False
            ))
        
        return results, total
    
    def get_article_by_id(self, article_id: int) -> Optional[ArticleResponseDTO]:
        """Récupère un article par son ID"""
        article = self.db.query(Article).filter_by(id=article_id).first()
        
        if not article:
            return None
        
        # Note: On ne récupère pas le statut ici car il dépend de l'utilisateur
        return ArticleResponseDTO(
            id=article.id,
            titre=article.titre,
            lien=article.lien,
            auteur=article.auteur,
            resume=article.resume,
            contenu=article.contenu,
            publie_le=article.publie_le,
            flux_id=article.flux_id,
            flux_nom=article.flux.nom,
            est_lu=False,
            est_favori=False
        )
    
    def user_can_read_article(self, user_id: int, article_id: int) -> bool:
        """Vérifie si un utilisateur peut lire un article"""
        article = self.db.query(Article).join(
            FluxRss
        ).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Article.id == article_id,
            Categorie.utilisateur_id == user_id
        ).first()
        
        return article is not None
    
    def mark_article_as_read(self, user_id: int, article_id: int):
        """Marque un article comme lu"""
        statut = self.db.query(StatutUtilisateurArticle).filter_by(
            utilisateur_id=user_id,
            article_id=article_id
        ).first()
        
        if not statut:
            statut = StatutUtilisateurArticle(
                utilisateur_id=user_id,
                article_id=article_id,
                est_lu=True,
                lu_le=datetime.utcnow()
            )
            self.db.add(statut)
        else:
            statut.est_lu = True
            statut.lu_le = datetime.utcnow()
        
        self.db.commit()
    
    def mark_article_as_unread(self, user_id: int, article_id: int):
        """Marque un article comme non lu"""
        statut = self.db.query(StatutUtilisateurArticle).filter_by(
            utilisateur_id=user_id,
            article_id=article_id
        ).first()
        
        if statut:
            statut.est_lu = False
            statut.lu_le = None
            self.db.commit()
    
    def add_article_to_favorites(self, user_id: int, article_id: int):
        """Ajoute un article aux favoris"""
        statut = self.db.query(StatutUtilisateurArticle).filter_by(
            utilisateur_id=user_id,
            article_id=article_id
        ).first()
        
        if not statut:
            statut = StatutUtilisateurArticle(
                utilisateur_id=user_id,
                article_id=article_id,
                est_favori=True,
                mis_en_favori_le=datetime.utcnow()
            )
            self.db.add(statut)
        else:
            statut.est_favori = True
            statut.mis_en_favori_le = datetime.utcnow()
        
        self.db.commit()
    
    def remove_article_from_favorites(self, user_id: int, article_id: int):
        """Retire un article des favoris"""
        statut = self.db.query(StatutUtilisateurArticle).filter_by(
            utilisateur_id=user_id,
            article_id=article_id
        ).first()
        
        if statut:
            statut.est_favori = False
            statut.mis_en_favori_le = None
            self.db.commit()
    
    def mark_articles_as_read(self, user_id: int, article_ids: List[int]):
        """Marque plusieurs articles comme lus"""
        for article_id in article_ids:
            self.mark_article_as_read(user_id, article_id)
    
    def mark_articles_as_unread(self, user_id: int, article_ids: List[int]):
        """Marque plusieurs articles comme non lus"""
        for article_id in article_ids:
            self.mark_article_as_unread(user_id, article_id)
    
    def add_articles_to_favorites(self, user_id: int, article_ids: List[int]):
        """Ajoute plusieurs articles aux favoris"""
        for article_id in article_ids:
            self.add_article_to_favorites(user_id, article_id)
    
    def remove_articles_from_favorites(self, user_id: int, article_ids: List[int]):
        """Retire plusieurs articles des favoris"""
        for article_id in article_ids:
            self.remove_article_from_favorites(user_id, article_id)
    
    def get_user_favorites(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ArticleResponseDTO]:
        """Récupère les articles favoris de l'utilisateur"""
        articles = self.db.query(Article).join(
            StatutUtilisateurArticle
        ).filter(
            StatutUtilisateurArticle.utilisateur_id == user_id,
            StatutUtilisateurArticle.est_favori == True
        ).order_by(
            StatutUtilisateurArticle.mis_en_favori_le.desc()
        ).offset(offset).limit(limit).all()
        
        results = []
        for article in articles:
            results.append(ArticleResponseDTO(
                id=article.id,
                titre=article.titre,
                lien=article.lien,
                auteur=article.auteur,
                resume=article.resume,
                contenu=article.contenu,
                publie_le=article.publie_le,
                flux_id=article.flux_id,
                flux_nom=article.flux.nom,
                est_lu=True,  # Forcément lu si en favori
                est_favori=True
            ))
        
        return results
    
    def get_unread_count(
        self,
        user_id: int,
        categorie_id: Optional[int] = None,
        flux_id: Optional[int] = None
    ) -> int:
        """Compte les articles non lus"""
        query = self.db.query(Article).join(
            FluxRss
        ).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id
        )
        
        if categorie_id:
            query = query.filter(Categorie.id == categorie_id)
        
        if flux_id:
            query = query.filter(FluxRss.id == flux_id)
        
        # Joindre les statuts
        query = query.outerjoin(
            StatutUtilisateurArticle,
            and_(
                StatutUtilisateurArticle.article_id == Article.id,
                StatutUtilisateurArticle.utilisateur_id == user_id
            )
        ).filter(
            or_(
                StatutUtilisateurArticle.est_lu == False,
                StatutUtilisateurArticle.est_lu.is_(None)
            )
        )
        
        return query.count()
    
    def import_opml(self, user_id: int, opml_content: bytes) -> int:
        """Importe des flux depuis un fichier OPML"""
        try:
            root = ET.fromstring(opml_content)
            imported_count = 0
            
            # Obtenir la catégorie par défaut
            categorie = self.db.query(Categorie).filter_by(
                utilisateur_id=user_id,
                nom="Non classé"
            ).first()
            
            if not categorie:
                categorie = Categorie(
                    nom="Non classé",
                    utilisateur_id=user_id,
                    couleur="#007bff"
                )
                self.db.add(categorie)
                self.db.flush()
            
            # Parser les outlines
            for outline in root.iter('outline'):
                xml_url = outline.get('xmlUrl')
                if xml_url:
                    # Vérifier si le flux n'existe pas déjà pour cet utilisateur
                    if not self.flux_exists_for_user(user_id, xml_url):
                        flux_data = FluxCreateDTO(
                            url=xml_url,
                            nom_personnalise=outline.get('text', ''),
                            categorie_id=categorie.id
                        )
                        self.create_flux(user_id, flux_data)
                        imported_count += 1
            
            # Enregistrer l'import
            journal = JournalImport(
                utilisateur_id=user_id,
                format='OPML',
                nom_fichier='import.opml',
                flux_importes=imported_count
            )
            self.db.add(journal)
            self.db.commit()
            
            return imported_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'import OPML: {e}")
            raise
    
    def fetch_all_user_flux_articles(self, user_id: int):
        """Récupère les articles de tous les flux de l'utilisateur"""
        flux_list = self.db.query(FluxRss).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id,
            FluxRss.est_actif == True
        ).all()
        
        for flux in flux_list:
            try:
                self.fetch_flux_articles(flux.id)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du flux {flux.id}: {e}")
    
    def export_to_opml(self, user_id: int) -> str:
        """Exporte les flux de l'utilisateur au format OPML"""
        flux_list = self.db.query(FluxRss).join(
            FluxCategorie
        ).join(
            Categorie
        ).filter(
            Categorie.utilisateur_id == user_id
        ).all()
        
        # Créer le document OPML
        opml = ET.Element('opml', version='2.0')
        head = ET.SubElement(opml, 'head')
        ET.SubElement(head, 'title').text = 'SUPRSS Export'
        ET.SubElement(head, 'dateCreated').text = datetime.utcnow().isoformat()
        
        body = ET.SubElement(opml, 'body')
        
        for flux in flux_list:
            ET.SubElement(body, 'outline',
                text=flux.nom,
                title=flux.nom,
                type='rss',
                xmlUrl=flux.url,
                htmlUrl=flux.url
            )
        
        # Enregistrer l'export
        journal = JournalExport(
            utilisateur_id=user_id,
            format='OPML',
            nom_fichier='export.opml'
        )
        self.db.add(journal)
        self.db.commit()
        
        return ET.tostring(opml, encoding='unicode')
    
    # Méthodes privées
    def _parse_feed_info(self, url: str) -> Dict[str, str]:
        """Parse les informations basiques d'un flux"""
        try:
            feed = feedparser.parse(url)
            return {
                'title': feed.feed.get('title', 'Sans titre'),
                'description': feed.feed.get('description', '')
            }
        except:
            return {'title': 'Flux RSS', 'description': ''}