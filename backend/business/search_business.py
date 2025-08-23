# business/search_business.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.user import Utilisateur
from models.rss import Article, FluxRss
from models.collection import Collection
from models.interaction import CommentaireArticle, StatutUtilisateurArticle
from models.category import Categorie, FluxCategorie
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
                        "est_favori": statut.est_favori if statut else False
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
                        "nombre_articles": len(flux.article) if flux.article else 0
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
            
            collections = self.db.query(Collection).filter(
                or_(
                    Collection.proprietaire_id == user_id,
                    and_(
                        Collection.est_partagee == True,
                        Collection.membre_collection.any(utilisateur_id=user_id)
                    )
                ),
                or_(
                    Collection.nom.ilike(search_pattern),
                    Collection.description.ilike(search_pattern)
                )
            ).limit(limit).all()
            
            results = []
            for collection in collections:
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
                        "nombre_flux": len(collection.collection_flux),
                        "nombre_membres": len(collection.membre_collection)
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
            
            comments = self.db.query(CommentaireArticle).join(
                Collection
            ).filter(
                or_(
                    Collection.proprietaire_id == user_id,
                    Collection.membre_collection.any(utilisateur_id=user_id)
                ),
                CommentaireArticle.contenu.ilike(search_pattern)
            ).limit(limit).all()
            
            results = []
            for comment in comments:
                results.append(SearchResultDTO(
                    type="comment",
                    id=comment.id,
                    title=f"Commentaire sur {comment.article.titre[:50]}",
                    description=comment.contenu[:200],
                    url=None,
                    match_snippet=self._extract_snippet(comment.contenu, query),
                    relevance_score=self._calculate_relevance_comment(comment, query),
                    metadata={
                        "article_id": comment.article_id,
                        "collection_id": comment.collection_id,
                        "utilisateur_id": comment.utilisateur_id,
                        "cree_le": comment.cree_le.isoformat()
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
            
            # Base query
            query_obj = self.db.query(Article)
            
            # Filtrer par flux de l'utilisateur
            user_flux_ids = self.db.query(FluxCategorie.flux_id).join(
                Categorie
            ).filter(
                Categorie.utilisateur_id == user_id
            )
            
            if category_id:
                user_flux_ids = user_flux_ids.filter(
                    Categorie.id == category_id
                )
            
            user_flux_ids = user_flux_ids.subquery()
            query_obj = query_obj.filter(Article.flux_id.in_(user_flux_ids))
            
            # Filtre par flux spécifique
            if flux_id:
                query_obj = query_obj.filter(Article.flux_id == flux_id)
            
            # Filtre par dates
            if date_from:
                query_obj = query_obj.filter(Article.publie_le >= datetime.fromisoformat(date_from))
            if date_to:
                query_obj = query_obj.filter(Article.publie_le <= datetime.fromisoformat(date_to))
            
            # Filtre par statut
            if only_unread or only_favorites:
                query_obj = query_obj.join(StatutUtilisateurArticle)
                query_obj = query_obj.filter(
                    StatutUtilisateurArticle.utilisateur_id == user_id
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
            
            # Pagination
            articles = query_obj.offset(offset).limit(limit).all()
            
            results = []
            for article in articles:
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
                        "flux_nom": article.flux.nom,
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
                        "nombre_articles": self.db.query(Article).filter(
                            Article.flux_id == flux.id
                        ).count()
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
                            Collection.membre_collection.any(utilisateur_id=user_id)
                        )
                    )
                query_obj = query_obj.filter(or_(*conditions))
            
            collections = query_obj.limit(limit).all()
            
            results = []
            for collection in collections:
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
                        "proprietaire_nom": collection.proprietaire.nom_utilisateur,
                        "nombre_flux": len(collection.collection_flux),
                        "nombre_membres": len(collection.membre_collection),
                        "cree_le": collection.cree_le.isoformat()
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
                    suggestions.add(name)
            
            if search_type in ["all", "collections"]:
                # Suggestions depuis les noms de collections
                collection_names = self.db.query(Collection.nom).filter(
                    or_(
                        Collection.proprietaire_id == user_id,
                        Collection.membre_collection.any(utilisateur_id=user_id)
                    ),
                    Collection.nom.ilike(pattern)
                ).limit(limit).all()
                
                for name, in collection_names:
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
        raise NotImplementedError("Les recherches sauvegardées ne sont pas encore implémentées")
    
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
        return {
            "total_searches": 0,
            "favorite_terms": [],
            "most_searched_type": "articles",
            "last_search": None
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