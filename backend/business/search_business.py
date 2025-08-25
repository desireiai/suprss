# business/search_business.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging


from models import (
    Utilisateur, 
    Article, 
    FluxRss, 
    Collection, 
    CommentaireArticle, 
    StatutUtilisateurArticle,
    Categorie, 
    FluxCategorie,
    CollectionFlux,
    MembreCollection
)
from dtos.search_dto import SearchResultDTO

logger = logging.getLogger(__name__)

class SearchBusiness:
    """Logique métier pour la recherche"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_articles(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[SearchResultDTO]:
        """Recherche basique dans les articles de l'utilisateur"""
        try:
            search_pattern = f"%{query}%"
            
            # Récupérer les flux de l'utilisateur via les catégories
            user_flux_ids = self.db.query(FluxCategorie.flux_id).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id
            ).subquery()
            
            articles = self.db.query(Article).filter(
                Article.flux_id.in_(user_flux_ids),
                or_(
                    Article.titre.ilike(search_pattern),
                    Article.contenu.ilike(search_pattern),
                    Article.resume.ilike(search_pattern)
                )
            ).limit(limit).all()
            
            results = []
            for article in articles:
                # Récupérer le statut de lecture
                statut = self.db.query(StatutUtilisateurArticle).filter(
                    StatutUtilisateurArticle.utilisateur_id == user_id,
                    StatutUtilisateurArticle.article_id == article.id
                ).first()
                
                results.append(SearchResultDTO(
                    type="article",
                    id=article.id,
                    title=article.titre,
                    description=article.resume[:200] if article.resume else None,
                    url=article.lien,
                    match_snippet=self._extract_snippet(article.contenu or article.resume, query),
                    relevance_score=self._calculate_relevance(article, query),
                    metadata={
                        "flux_id": article.flux_id,
                        "publie_le": article.publie_le.isoformat() if article.publie_le else None,
                        "est_lu": statut.est_lu if statut else False,
                        "est_favori": statut.est_favori if statut else False,
                        "auteur": article.auteur
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'articles: {e}")
            return []
    
    def search_flux(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[SearchResultDTO]:
        """Recherche dans les flux RSS de l'utilisateur"""
        try:
            search_pattern = f"%{query}%"
            
            flux_list = self.db.query(FluxRss).join(
                FluxCategorie
            ).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id,
                or_(
                    FluxRss.nom.ilike(search_pattern),
                    FluxRss.description.ilike(search_pattern),
                    FluxRss.url.ilike(search_pattern)
                )
            ).limit(limit).all()
            
            results = []
            for flux in flux_list:
                # Compter le nombre d'articles pour ce flux
                nombre_articles = self.db.query(func.count(Article.id)).filter(
                    Article.flux_id == flux.id
                ).scalar() or 0
                
                results.append(SearchResultDTO(
                    type="flux",
                    id=flux.id,
                    title=flux.nom,
                    description=flux.description[:200] if flux.description else None,
                    url=flux.url,
                    match_snippet=None,
                    relevance_score=self._calculate_relevance_flux(flux, query),
                    metadata={
                        "est_actif": flux.est_actif,
                        "derniere_maj": flux.derniere_maj.isoformat() if flux.derniere_maj else None,
                        "nombre_articles": nombre_articles,
                        "frequence_maj_heures": flux.frequence_maj_heures
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de flux: {e}")
            return []
    
    def search_collections(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[SearchResultDTO]:
        """Recherche dans les collections accessibles à l'utilisateur"""
        try:
            search_pattern = f"%{query}%"
            
            # Collections possédées par l'utilisateur ou auxquelles il participe
            collections = self.db.query(Collection).filter(
                or_(
                    Collection.proprietaire_id == user_id,
                    and_(
                        Collection.est_partagee == True,
                        Collection.id.in_(
                            self.db.query(MembreCollection.collection_id).filter(
                                MembreCollection.utilisateur_id == user_id
                            )
                        )
                    )
                ),
                or_(
                    Collection.nom.ilike(search_pattern),
                    Collection.description.ilike(search_pattern)
                )
            ).limit(limit).all()
            
            results = []
            for collection in collections:
                # Compter les flux et membres
                nombre_flux = self.db.query(func.count(CollectionFlux.id)).filter(
                    CollectionFlux.collection_id == collection.id
                ).scalar() or 0
                
                nombre_membres = self.db.query(func.count(MembreCollection.id)).filter(
                    MembreCollection.collection_id == collection.id
                ).scalar() or 0
                
                results.append(SearchResultDTO(
                    type="collection",
                    id=collection.id,
                    title=collection.nom,
                    description=collection.description[:200] if collection.description else None,
                    url=None,
                    match_snippet=None,
                    relevance_score=self._calculate_relevance_collection(collection, query),
                    metadata={
                        "est_partagee": collection.est_partagee,
                        "proprietaire_id": collection.proprietaire_id,
                        "nombre_flux": nombre_flux,
                        "nombre_membres": nombre_membres,
                        "cree_le": collection.cree_le.isoformat() if collection.cree_le else None
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de collections: {e}")
            return []
    
    def search_comments(
        self,
        user_id: int,
        query: str,
        limit: int = 10
    ) -> List[SearchResultDTO]:
        """Recherche dans les commentaires accessibles à l'utilisateur"""
        try:
            search_pattern = f"%{query}%"
            
            # Commentaires dans les collections accessibles
            comments = self.db.query(CommentaireArticle).join(
                Collection
            ).filter(
                or_(
                    Collection.proprietaire_id == user_id,
                    Collection.id.in_(
                        self.db.query(MembreCollection.collection_id).filter(
                            MembreCollection.utilisateur_id == user_id
                        )
                    )
                ),
                CommentaireArticle.contenu.ilike(search_pattern)
            ).limit(limit).all()
            
            results = []
            for comment in comments:
                # Récupérer le titre de l'article associé
                article_titre = self.db.query(Article.titre).filter(
                    Article.id == comment.article_id
                ).scalar() or "Article inconnu"
                
                results.append(SearchResultDTO(
                    type="comment",
                    id=comment.id,
                    title=f"Commentaire sur {article_titre[:50]}",
                    description=comment.contenu[:200],
                    url=None,
                    match_snippet=self._extract_snippet(comment.contenu, query),
                    relevance_score=self._calculate_relevance_comment(comment, query),
                    metadata={
                        "article_id": comment.article_id,
                        "collection_id": comment.collection_id,
                        "utilisateur_id": comment.utilisateur_id,
                        "cree_le": comment.cree_le.isoformat() if comment.cree_le else None
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de commentaires: {e}")
            return []
    
    def search_articles_advanced(
        self,
        user_id: int,
        query: str,
        category_id: Optional[int] = None,
        flux_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        only_unread: bool = False,
        only_favorites: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[SearchResultDTO]:
        """Recherche avancée dans les articles avec filtres"""
        try:
            search_pattern = f"%{query}%"
            
            # Base query avec jointure pour accéder aux flux de l'utilisateur
            query_obj = self.db.query(Article).join(
                FluxCategorie, Article.flux_id == FluxCategorie.flux_id
            ).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id
            )
            
            # Filtre par catégorie
            if category_id:
                query_obj = query_obj.filter(Categorie.id == category_id)
            
            # Filtre par flux spécifique
            if flux_id:
                query_obj = query_obj.filter(Article.flux_id == flux_id)
            
            # Filtre par dates
            if date_from:
                try:
                    date_from_parsed = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    query_obj = query_obj.filter(Article.publie_le >= date_from_parsed)
                except ValueError:
                    logger.warning(f"Format de date invalide pour date_from: {date_from}")
                    
            if date_to:
                try:
                    date_to_parsed = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    query_obj = query_obj.filter(Article.publie_le <= date_to_parsed)
                except ValueError:
                    logger.warning(f"Format de date invalide pour date_to: {date_to}")
            
            # Filtre par statut (non-lu/favoris)
            if only_unread or only_favorites:
                # Utiliser LEFT JOIN pour inclure les articles sans statut
                query_obj = query_obj.outerjoin(
                    StatutUtilisateurArticle,
                    and_(
                        StatutUtilisateurArticle.article_id == Article.id,
                        StatutUtilisateurArticle.utilisateur_id == user_id
                    )
                )
                
                if only_unread:
                    query_obj = query_obj.filter(
                        or_(
                            StatutUtilisateurArticle.est_lu == False,
                            StatutUtilisateurArticle.est_lu.is_(None)
                        )
                    )
                if only_favorites:
                    query_obj = query_obj.filter(
                        StatutUtilisateurArticle.est_favori == True
                    )
            
            # Recherche textuelle
            query_obj = query_obj.filter(
                or_(
                    Article.titre.ilike(search_pattern),
                    Article.contenu.ilike(search_pattern),
                    Article.resume.ilike(search_pattern),
                    Article.auteur.ilike(search_pattern)
                )
            )
            
            # Pagination avec tri par date de publication
            articles = query_obj.order_by(desc(Article.publie_le)).offset(offset).limit(limit).all()
            
            results = []
            for article in articles:
                # Récupérer le statut spécifiquement pour chaque article
                statut = self.db.query(StatutUtilisateurArticle).filter(
                    StatutUtilisateurArticle.utilisateur_id == user_id,
                    StatutUtilisateurArticle.article_id == article.id
                ).first()
                
                # Récupérer le nom du flux
                flux_nom = self.db.query(FluxRss.nom).filter(
                    FluxRss.id == article.flux_id
                ).scalar() or "Flux inconnu"
                
                results.append(SearchResultDTO(
                    type="article",
                    id=article.id,
                    title=article.titre,
                    description=article.resume[:200] if article.resume else None,
                    url=article.lien,
                    match_snippet=self._extract_snippet(article.contenu or article.resume, query),
                    relevance_score=self._calculate_relevance(article, query),
                    metadata={
                        "flux_id": article.flux_id,
                        "flux_nom": flux_nom,
                        "auteur": article.auteur,
                        "publie_le": article.publie_le.isoformat() if article.publie_le else None,
                        "est_lu": statut.est_lu if statut else False,
                        "est_favori": statut.est_favori if statut else False
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche avancée d'articles: {e}")
            return []
    
    def search_flux_advanced(
        self,
        user_id: int,
        query: str,
        category_id: Optional[int] = None,
        only_active: bool = True,
        limit: int = 20
    ) -> List[SearchResultDTO]:
        """Recherche avancée dans les flux"""
        try:
            search_pattern = f"%{query}%"
            
            query_obj = self.db.query(FluxRss).join(
                FluxCategorie
            ).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id,
                or_(
                    FluxRss.nom.ilike(search_pattern),
                    FluxRss.description.ilike(search_pattern),
                    FluxRss.url.ilike(search_pattern)
                )
            )
            
            if category_id:
                query_obj = query_obj.filter(Categorie.id == category_id)
            
            if only_active:
                query_obj = query_obj.filter(FluxRss.est_actif == True)
            
            flux_list = query_obj.limit(limit).all()
            
            results = []
            for flux in flux_list:
                # Compter les articles pour ce flux
                nombre_articles = self.db.query(func.count(Article.id)).filter(
                    Article.flux_id == flux.id
                ).scalar() or 0
                
                results.append(SearchResultDTO(
                    type="flux",
                    id=flux.id,
                    title=flux.nom,
                    description=flux.description[:200] if flux.description else None,
                    url=flux.url,
                    match_snippet=None,
                    relevance_score=self._calculate_relevance_flux(flux, query),
                    metadata={
                        "est_actif": flux.est_actif,
                        "frequence_maj_heures": flux.frequence_maj_heures,
                        "derniere_maj": flux.derniere_maj.isoformat() if flux.derniere_maj else None,
                        "nombre_articles": nombre_articles
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche avancée de flux: {e}")
            return []
    
    def search_collections_advanced(
        self,
        user_id: int,
        query: str,
        only_owned: bool = False,
        include_shared: bool = True,
        limit: int = 20
    ) -> List[SearchResultDTO]:
        """Recherche avancée dans les collections"""
        try:
            search_pattern = f"%{query}%"
            
            query_obj = self.db.query(Collection).filter(
                or_(
                    Collection.nom.ilike(search_pattern),
                    Collection.description.ilike(search_pattern)
                )
            )
            
            if only_owned:
                query_obj = query_obj.filter(Collection.proprietaire_id == user_id)
            else:
                conditions = [Collection.proprietaire_id == user_id]
                if include_shared:
                    conditions.append(
                        and_(
                            Collection.est_partagee == True,
                            Collection.id.in_(
                                self.db.query(MembreCollection.collection_id).filter(
                                    MembreCollection.utilisateur_id == user_id
                                )
                            )
                        )
                    )
                query_obj = query_obj.filter(or_(*conditions))
            
            collections = query_obj.limit(limit).all()
            
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
                
                results.append(SearchResultDTO(
                    type="collection",
                    id=collection.id,
                    title=collection.nom,
                    description=collection.description[:200] if collection.description else None,
                    url=None,
                    match_snippet=None,
                    relevance_score=self._calculate_relevance_collection(collection, query),
                    metadata={
                        "est_partagee": collection.est_partagee,
                        "proprietaire_id": collection.proprietaire_id,
                        "proprietaire_nom": proprietaire_nom,
                        "nombre_flux": nombre_flux,
                        "nombre_membres": nombre_membres,
                        "cree_le": collection.cree_le.isoformat() if collection.cree_le else None
                    }
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche avancée de collections: {e}")
            return []
    
    def get_search_suggestions(
        self,
        user_id: int,
        query_prefix: str,
        search_type: str = "all",
        limit: int = 10
    ) -> List[str]:
        """Récupère des suggestions de recherche basées sur les données existantes"""
        try:
            suggestions = set()
            pattern = f"{query_prefix}%"
            
            if search_type in ["all", "articles"]:
                # Suggestions depuis les titres d'articles
                article_titles = self.db.query(Article.titre).join(
                    FluxCategorie, Article.flux_id == FluxCategorie.flux_id
                ).join(
                    Categorie
                ).filter(
                    Categorie.utilisateur_id == user_id,
                    Article.titre.ilike(pattern)
                ).limit(limit).all()
                
                for title, in article_titles:
                    if title:
                        suggestions.add(title[:100])
            
            if search_type in ["all", "flux"]:
                # Suggestions depuis les noms de flux
                flux_names = self.db.query(FluxRss.nom).join(
                    FluxCategorie
                ).join(
                    Categorie
                ).filter(
                    Categorie.utilisateur_id == user_id,
                    FluxRss.nom.ilike(pattern)
                ).limit(limit).all()
                
                for name, in flux_names:
                    if name:
                        suggestions.add(name)
            
            if search_type in ["all", "collections"]:
                # Suggestions depuis les noms de collections
                collection_names = self.db.query(Collection.nom).filter(
                    or_(
                        Collection.proprietaire_id == user_id,
                        Collection.id.in_(
                            self.db.query(MembreCollection.collection_id).filter(
                                MembreCollection.utilisateur_id == user_id
                            )
                        )
                    ),
                    Collection.nom.ilike(pattern)
                ).limit(limit).all()
                
                for name, in collection_names:
                    if name:
                        suggestions.add(name)
            
            return list(suggestions)[:limit]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des suggestions: {e}")
            return []
    
    # Méthodes stub pour les fonctionnalités non implémentées
    def get_user_recent_searches(self, user_id: int, limit: int = 10) -> List[str]:
        """Non implémenté - nécessiterait une table d'historique"""
        return []
    
    def clear_user_search_history(self, user_id: int):
        """Non implémenté - nécessiterait une table d'historique"""
        pass
    
    def get_trending_searches(self, period: str = "week", limit: int = 10) -> List[Dict[str, Any]]:
        """Non implémenté - nécessiterait une table d'historique"""
        return []
    
    def save_search(self, user_id: int, query: str, name: str) -> Dict[str, Any]:
        """Non implémenté - nécessiterait une table de recherches sauvegardées"""
        class MockSavedSearch:
            def __init__(self):
                self.id = 1
        return MockSavedSearch()
    
    def get_user_saved_searches(self, user_id: int) -> List[Dict[str, Any]]:
        """Non implémenté - nécessiterait une table de recherches sauvegardées"""
        return []
    
    def user_owns_saved_search(self, user_id: int, search_id: int) -> bool:
        """Non implémenté - nécessiterait une table de recherches sauvegardées"""
        return False
    
    def delete_saved_search(self, search_id: int):
        """Non implémenté - nécessiterait une table de recherches sauvegardées"""
        pass
    
    def get_user_search_stats(self, user_id: int) -> Dict[str, Any]:
        """Statistiques basiques sans table d'historique"""
        try:
            # Calculer quelques statistiques basiques
            total_articles = self.db.query(func.count(Article.id)).join(
                FluxCategorie, Article.flux_id == FluxCategorie.flux_id
            ).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id
            ).scalar() or 0
            
            total_flux = self.db.query(func.count(FluxRss.id)).join(
                FluxCategorie
            ).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id
            ).scalar() or 0
            
            return {
                "total_searches": 0,
                "favorite_terms": [],
                "most_searched_type": "articles",
                "last_search": None,
                "total_articles": total_articles,
                "total_flux": total_flux
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}")
            return {
                "total_searches": 0,
                "favorite_terms": [],
                "most_searched_type": "articles",
                "last_search": None,
                "total_articles": 0,
                "total_flux": 0
            }
    
    def rebuild_user_search_index(self, user_id: int):
        """Non nécessaire sans système d'indexation séparé"""
        logger.info(f"Rebuild index appelé pour l'utilisateur {user_id} - non nécessaire")
    
    # Méthodes utilitaires privées
    def _extract_snippet(self, text: Optional[str], query: str, context_length: int = 150) -> Optional[str]:
        """Extrait un snippet du texte autour du terme recherché"""
        if not text:
            return None
        
        text_lower = text.lower()
        query_lower = query.lower()
        
        index = text_lower.find(query_lower)
        if index == -1:
            return text[:context_length] + "..." if len(text) > context_length else text
        
        start = max(0, index - context_length // 2)
        end = min(len(text), index + len(query) + context_length // 2)
        
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _calculate_relevance(self, article: Article, query: str) -> float:
        """Calcule la pertinence d'un article"""
        score = 0.0
        query_lower = query.lower()
        
        if article.titre and query_lower in article.titre.lower():
            score += 3.0
        if article.resume and query_lower in article.resume.lower():
            score += 2.0
        if article.contenu and query_lower in article.contenu.lower():
            score += 1.0
        if article.auteur and query_lower in article.auteur.lower():
            score += 1.5
        
        return score
    
    def _calculate_relevance_flux(self, flux: FluxRss, query: str) -> float:
        """Calcule la pertinence d'un flux"""
        score = 0.0
        query_lower = query.lower()
        
        if flux.nom and query_lower in flux.nom.lower():
            score += 3.0
        if flux.description and query_lower in flux.description.lower():
            score += 2.0
        if flux.url and query_lower in flux.url.lower():
            score += 1.0
        
        return score
    
    def _calculate_relevance_collection(self, collection: Collection, query: str) -> float:
        """Calcule la pertinence d'une collection"""
        score = 0.0
        query_lower = query.lower()
        
        if collection.nom and query_lower in collection.nom.lower():
            score += 3.0
        if collection.description and query_lower in collection.description.lower():
            score += 2.0
        
        return score
    
    def _calculate_relevance_comment(self, comment: CommentaireArticle, query: str) -> float:
        """Calcule la pertinence d'un commentaire"""
        return 2.0 if comment.contenu and query.lower() in comment.contenu.lower() else 0.0