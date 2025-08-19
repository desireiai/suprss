# business/rss_business.py
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from ..models.rss import FluxRss, Article
from ..models.category import Categorie, FluxCategorie
from ..models.collection import Collection, CollectionFlux, MembreCollection
from ..models.interaction import StatutUtilisateurArticle
import feedparser
import hashlib
from urllib.parse import urlparse
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configuration du logger
logger = logging.getLogger(__name__)

class RssBusiness:
    """Logique métier pour la gestion des flux RSS"""
    
    def __init__(self, db: Session, scheduler: Optional[BackgroundScheduler] = None):
        self.db = db
        self.scheduler = scheduler or BackgroundScheduler()
        self._init_scheduler()
    
    def add_flux(self, 
                url: str,
                user_id: int,
                categorie_id: Optional[int] = None,
                nom_personnalise: Optional[str] = None,
                frequence_maj_heures: int = 6) -> FluxRss:
        """Ajouter un nouveau flux RSS"""
        
        # Valider l'URL
        if not self._validate_url(url):
            raise ValueError("URL invalide")
        
        # Vérifier si le flux existe déjà
        flux = self.db.query(FluxRss).filter_by(url=url).first()
        
        if not flux:
            # Parser le flux pour obtenir les informations
            feed_data = self._parse_feed(url)
            
            if not feed_data:
                raise ValueError("Impossible de parser le flux RSS")
            
            flux = FluxRss(
                nom=nom_personnalise or feed_data.get('title', 'Flux sans titre'),
                url=url,
                description=feed_data.get('description', ''),
                frequence_maj_heures=frequence_maj_heures,
                derniere_maj=datetime.utcnow()
            )
            
            self.db.add(flux)
            self.db.flush()
            
            # Récupérer les articles initiaux
            self._fetch_articles(flux)
            
            # Ajouter à la planification si nouveau flux
            self._schedule_single_flux_update(flux)
        
        # Associer à la catégorie de l'utilisateur
        if not categorie_id:
            # Utiliser la catégorie par défaut
            categorie = self.db.query(Categorie).filter_by(
                utilisateur_id=user_id,
                nom="Non classé"
            ).first()
            categorie_id = categorie.id if categorie else None
        
        if categorie_id:
            # Vérifier que la catégorie appartient à l'utilisateur
            categorie = self.db.query(Categorie).filter_by(
                id=categorie_id,
                utilisateur_id=user_id
            ).first()
            
            if not categorie:
                raise ValueError("Catégorie invalide")
            
            # Vérifier si l'association existe déjà
            existing = self.db.query(FluxCategorie).filter_by(
                flux_id=flux.id,
                categorie_id=categorie_id
            ).first()
            
            if not existing:
                flux_cat = FluxCategorie(
                    flux_id=flux.id,
                    categorie_id=categorie_id
                )
                self.db.add(flux_cat)
        
        self.db.commit()
        return flux
    
    def update_flux(self, flux_id: int, force: bool = False) -> int:
        """
        Mettre à jour un flux RSS et récupérer les nouveaux articles
        
        Args:
            flux_id: ID du flux à mettre à jour
            force: Si True, ignore la fréquence de mise à jour
        """
        flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
        
        if not flux or not flux.est_actif:
            return 0
        
        # Vérifier la fréquence de mise à jour (sauf si forcé)
        if not force and flux.derniere_maj:
            delta = datetime.utcnow() - flux.derniere_maj
            if delta < timedelta(hours=flux.frequence_maj_heures):
                logger.info(f"Flux {flux_id} ignoré - dernière MAJ trop récente")
                return 0
        
        try:
            new_articles = self._fetch_articles(flux)
            flux.derniere_maj = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Flux {flux_id} mis à jour - {new_articles} nouveaux articles")
            return new_articles
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du flux {flux_id}: {str(e)}")
            self.db.rollback()
            return 0
    
    def update_all_flux(self) -> Dict[str, int]:
        """Mettre à jour tous les flux actifs"""
        flux_list = self.db.query(FluxRss).filter_by(est_actif=True).all()
        results = {
            'updated': 0,
            'new_articles': 0,
            'errors': 0
        }
        
        for flux in flux_list:
            try:
                new_articles = self.update_flux(flux.id)
                if new_articles > 0:
                    results['updated'] += 1
                    results['new_articles'] += new_articles
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du flux {flux.id}: {str(e)}")
                results['errors'] += 1
        
        return results
    
    def mark_article_read(self, user_id: int, article_id: int) -> StatutUtilisateurArticle:
        """Marquer un article comme lu"""
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
        return statut
    
    def mark_articles_bulk(self, 
                          user_id: int, 
                          article_ids: List[int], 
                          action: str) -> int:
        """
        Marquer plusieurs articles en masse
        
        Args:
            user_id: ID de l'utilisateur
            article_ids: Liste des IDs d'articles
            action: 'mark_read', 'mark_unread', 'add_favorite', 'remove_favorite'
        
        Returns:
            Nombre d'articles modifiés
        """
        count = 0
        
        for article_id in article_ids:
            try:
                statut = self.db.query(StatutUtilisateurArticle).filter_by(
                    utilisateur_id=user_id,
                    article_id=article_id
                ).first()
                
                if not statut:
                    statut = StatutUtilisateurArticle(
                        utilisateur_id=user_id,
                        article_id=article_id
                    )
                    self.db.add(statut)
                
                if action == 'mark_read':
                    statut.est_lu = True
                    statut.lu_le = datetime.utcnow()
                elif action == 'mark_unread':
                    statut.est_lu = False
                    statut.lu_le = None
                elif action == 'add_favorite':
                    statut.est_favori = True
                    statut.mis_en_favori_le = datetime.utcnow()
                elif action == 'remove_favorite':
                    statut.est_favori = False
                    statut.mis_en_favori_le = None
                
                count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors du marquage de l'article {article_id}: {str(e)}")
                continue
        
        self.db.commit()
        return count
    
    def toggle_favorite(self, user_id: int, article_id: int) -> StatutUtilisateurArticle:
        """Basculer le statut favori d'un article"""
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
            statut.est_favori = not statut.est_favori
            statut.mis_en_favori_le = datetime.utcnow() if statut.est_favori else None
        
        self.db.commit()
        return statut
    
    def get_user_articles(self, 
                         user_id: int,
                         categorie_id: Optional[int] = None,
                         flux_id: Optional[int] = None,
                         only_unread: bool = False,
                         only_favorites: bool = False,
                         date_debut: Optional[datetime] = None,
                         date_fin: Optional[datetime] = None,
                         limit: int = 50,
                         offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """
        Obtenir les articles pour un utilisateur avec filtres
        
        Returns:
            Tuple (articles, total_count)
        """
        
        # Construire la requête de base
        query = self.db.query(Article).join(FluxRss).join(FluxCategorie).join(Categorie)
        
        # Filtrer par utilisateur
        query = query.filter(Categorie.utilisateur_id == user_id)
        
        # Filtrer par catégorie si spécifiée
        if categorie_id:
            query = query.filter(Categorie.id == categorie_id)
        
        # Filtrer par flux si spécifié
        if flux_id:
            query = query.filter(FluxRss.id == flux_id)
        
        # Joindre les statuts
        query = query.outerjoin(
            StatutUtilisateurArticle,
            and_(
                StatutUtilisateurArticle.article_id == Article.id,
                StatutUtilisateurArticle.utilisateur_id == user_id
            )
        )
        
        # Filtrer par statut de lecture
        if only_unread:
            query = query.filter(
                or_(
                    StatutUtilisateurArticle.est_lu == False,
                    StatutUtilisateurArticle.est_lu == None
                )
            )
        
        # Filtrer par favoris
        if only_favorites:
            query = query.filter(StatutUtilisateurArticle.est_favori == True)
        
        # Filtrer par dates
        if date_debut:
            query = query.filter(Article.publie_le >= date_debut)
        if date_fin:
            query = query.filter(Article.publie_le <= date_fin)
        
        # Compter le total avant pagination
        total_count = query.count()
        
        # Ordonner par date de publication
        query = query.order_by(Article.publie_le.desc())
        
        # Pagination
        articles = query.limit(limit).offset(offset).all()
        
        # Formater les résultats
        results = []
        for article in articles:
            statut = self.db.query(StatutUtilisateurArticle).filter_by(
                utilisateur_id=user_id,
                article_id=article.id
            ).first()
            
            results.append({
                'id': article.id,
                'titre': article.titre,
                'lien': article.lien,
                'auteur': article.auteur,
                'resume': article.resume,
                'contenu': article.contenu,
                'publie_le': article.publie_le,
                'flux_nom': article.flux.nom,
                'flux_id': article.flux.id,
                'est_lu': statut.est_lu if statut else False,
                'est_favori': statut.est_favori if statut else False,
                'lu_le': statut.lu_le if statut else None,
                'mis_en_favori_le': statut.mis_en_favori_le if statut else None
            })
        
        return results, total_count
    
    def search_articles(self, 
                       user_id: int, 
                       query: str,
                       source: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Rechercher des articles avec des critères avancés"""
        search_pattern = f'%{query}%'
        
        # Requête de base
        articles_query = self.db.query(Article).join(FluxRss).join(FluxCategorie).join(Categorie)
        
        # Filtrer par utilisateur
        articles_query = articles_query.filter(Categorie.utilisateur_id == user_id)
        
        # Recherche textuelle
        articles_query = articles_query.filter(
            or_(
                Article.titre.ilike(search_pattern),
                Article.contenu.ilike(search_pattern),
                Article.resume.ilike(search_pattern),
                Article.auteur.ilike(search_pattern) if query else False
            )
        )
        
        # Filtrer par source si spécifiée
        if source:
            articles_query = articles_query.filter(FluxRss.nom.ilike(f'%{source}%'))
        
        # Filtrer par tags si spécifiés (à implémenter avec un système de tags)
        # TODO: Implémenter le système de tags
        
        # Ordonner par pertinence (date de publication par défaut)
        articles = articles_query.order_by(Article.publie_le.desc()).limit(100).all()
        
        results = []
        for article in articles:
            statut = self.db.query(StatutUtilisateurArticle).filter_by(
                utilisateur_id=user_id,
                article_id=article.id
            ).first()
            
            # Calculer un score de pertinence simple
            relevance_score = 0
            if query.lower() in article.titre.lower():
                relevance_score += 3
            if article.resume and query.lower() in article.resume.lower():
                relevance_score += 2
            if article.contenu and query.lower() in article.contenu.lower():
                relevance_score += 1
            
            results.append({
                'id': article.id,
                'titre': article.titre,
                'lien': article.lien,
                'resume': article.resume,
                'publie_le': article.publie_le,
                'flux_nom': article.flux.nom,
                'flux_id': article.flux.id,
                'est_lu': statut.est_lu if statut else False,
                'est_favori': statut.est_favori if statut else False,
                'relevance_score': relevance_score
            })
        
        # Trier par score de pertinence puis par date
        results.sort(key=lambda x: (-x['relevance_score'], x['publie_le']), reverse=True)
        
        return results
    
    def search_articles_in_collection(self, 
                                    collection_id: int,
                                    user_id: int,
                                    query: str,
                                    flux_id: Optional[int] = None,
                                    only_unread: bool = False,
                                    only_favorites: bool = False,
                                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        Rechercher des articles dans une collection spécifique
        
        Args:
            collection_id: ID de la collection
            user_id: ID de l'utilisateur effectuant la recherche
            query: Terme de recherche
            flux_id: Filtrer par un flux spécifique dans la collection
            only_unread: Afficher uniquement les articles non lus
            only_favorites: Afficher uniquement les favoris
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des articles trouvés avec leurs métadonnées
        """
        
        # Vérifier que l'utilisateur a accès à cette collection
        membre = self.db.query(MembreCollection).filter_by(
            collection_id=collection_id,
            utilisateur_id=user_id
        ).first()
        
        if not membre or not membre.peut_lire:
            raise PermissionError("Vous n'avez pas accès à cette collection")
        
        # Construire la requête de base pour les articles de la collection
        search_pattern = f'%{query}%'
        
        # Joindre les tables nécessaires
        articles_query = (
            self.db.query(Article)
            .join(FluxRss)
            .join(CollectionFlux)
            .filter(CollectionFlux.collection_id == collection_id)
        )
        
        # Filtrer par flux spécifique si demandé
        if flux_id:
            articles_query = articles_query.filter(FluxRss.id == flux_id)
        
        # Recherche textuelle dans titre, contenu, résumé et auteur
        if query:
            articles_query = articles_query.filter(
                or_(
                    Article.titre.ilike(search_pattern),
                    Article.contenu.ilike(search_pattern),
                    Article.resume.ilike(search_pattern),
                    Article.auteur.ilike(search_pattern),
                    FluxRss.nom.ilike(search_pattern)  # Recherche aussi dans le nom du flux
                )
            )
        
        # Joindre les statuts utilisateur
        articles_query = articles_query.outerjoin(
            StatutUtilisateurArticle,
            and_(
                StatutUtilisateurArticle.article_id == Article.id,
                StatutUtilisateurArticle.utilisateur_id == user_id
            )
        )
        
        # Filtrer par statut de lecture
        if only_unread:
            articles_query = articles_query.filter(
                or_(
                    StatutUtilisateurArticle.est_lu == False,
                    StatutUtilisateurArticle.est_lu == None
                )
            )
        
        # Filtrer par favoris
        if only_favorites:
            articles_query = articles_query.filter(
                StatutUtilisateurArticle.est_favori == True
            )
        
        # Ordonner par date de publication (plus récent en premier)
        articles_query = articles_query.order_by(Article.publie_le.desc())
        
        # Limiter les résultats
        articles = articles_query.limit(limit).all()
        
        # Formater les résultats
        results = []
        for article in articles:
            # Récupérer le statut de l'article pour cet utilisateur
            statut = self.db.query(StatutUtilisateurArticle).filter_by(
                utilisateur_id=user_id,
                article_id=article.id
            ).first()
            
            # Calculer un score de pertinence basé sur la position du terme
            relevance_score = 0
            if query:
                query_lower = query.lower()
                if query_lower in article.titre.lower():
                    relevance_score += 5  # Titre a le plus de poids
                if article.auteur and query_lower in article.auteur.lower():
                    relevance_score += 3  # Auteur est important
                if article.resume and query_lower in article.resume.lower():
                    relevance_score += 2  # Résumé est moyennement important
                if article.contenu and query_lower in article.contenu.lower():
                    relevance_score += 1  # Contenu a le moins de poids
                if query_lower in article.flux.nom.lower():
                    relevance_score += 2  # Nom du flux est pertinent
            
            # Créer un extrait avec le contexte de la recherche
            match_snippet = self._create_match_snippet(article, query) if query else None
            
            results.append({
                'id': article.id,
                'titre': article.titre,
                'lien': article.lien,
                'auteur': article.auteur,
                'resume': article.resume,
                'contenu': article.contenu,
                'publie_le': article.publie_le,
                'flux_id': article.flux.id,
                'flux_nom': article.flux.nom,
                'collection_id': collection_id,
                'est_lu': statut.est_lu if statut else False,
                'est_favori': statut.est_favori if statut else False,
                'lu_le': statut.lu_le if statut else None,
                'mis_en_favori_le': statut.mis_en_favori_le if statut else None,
                'relevance_score': relevance_score,
                'match_snippet': match_snippet
            })
        
        # Trier par score de pertinence puis par date
        if query:
            results.sort(key=lambda x: (-x['relevance_score'], x['publie_le']), reverse=True)
        
        logger.info(f"Recherche dans collection {collection_id}: '{query}' - {len(results)} résultats")
        
        return results
    
    def schedule_feed_updates(self, 
                            initial_delay_minutes: int = 1,
                            default_interval_hours: int = 1) -> Dict[str, Any]:
        """
        Planifier les mises à jour automatiques des flux RSS
        
        Cette méthode configure un système de planification qui :
        1. Vérifie régulièrement quels flux doivent être mis à jour
        2. Respecte la fréquence de mise à jour définie pour chaque flux
        3. Gère les erreurs et les tentatives de récupération
        
        Args:
            initial_delay_minutes: Délai avant la première exécution
            default_interval_hours: Intervalle par défaut entre les vérifications
        
        Returns:
            Informations sur la planification mise en place
        """
        
        try:
            # Arrêter les jobs existants si nécessaire
            existing_jobs = self.scheduler.get_jobs()
            for job in existing_jobs:
                if job.id.startswith('flux_update_'):
                    self.scheduler.remove_job(job.id)
            
            # Planifier la mise à jour globale périodique
            self.scheduler.add_job(
                func=self._scheduled_update_all_flux,
                trigger=IntervalTrigger(hours=default_interval_hours),
                id='flux_update_global',
                name='Mise à jour globale des flux RSS',
                replace_existing=True,
                max_instances=1,  # Éviter les exécutions simultanées
                misfire_grace_time=3600  # 1 heure de tolérance
            )
            
            # Planifier les mises à jour individuelles pour chaque flux selon sa fréquence
            flux_list = self.db.query(FluxRss).filter_by(est_actif=True).all()
            scheduled_count = 0
            
            for flux in flux_list:
                success = self._schedule_single_flux_update(flux)
                if success:
                    scheduled_count += 1
            
            # Démarrer le scheduler s'il n'est pas déjà en cours
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler démarré avec succès")
            
            # Planifier une mise à jour immédiate après le délai initial
            if initial_delay_minutes > 0:
                run_time = datetime.utcnow() + timedelta(minutes=initial_delay_minutes)
                self.scheduler.add_job(
                    func=self._scheduled_update_all_flux,
                    trigger='date',
                    run_date=run_time,
                    id='flux_update_initial',
                    name='Mise à jour initiale des flux'
                )
            
            result = {
                'status': 'success',
                'scheduler_running': self.scheduler.running,
                'total_flux': len(flux_list),
                'scheduled_flux': scheduled_count,
                'global_interval_hours': default_interval_hours,
                'initial_delay_minutes': initial_delay_minutes,
                'jobs': []
            }
            
            # Lister tous les jobs planifiés
            for job in self.scheduler.get_jobs():
                if job.id.startswith('flux_update_'):
                    result['jobs'].append({
                        'id': job.id,
                        'name': job.name,
                        'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                    })
            
            logger.info(f"Planification configurée: {scheduled_count}/{len(flux_list)} flux planifiés")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de la planification: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'scheduler_running': self.scheduler.running
            }
    
    def get_scheduled_updates_status(self) -> Dict[str, Any]:
        """
        Obtenir le statut actuel des mises à jour planifiées
        
        Returns:
            Informations sur les jobs planifiés et leur état
        """
        
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            if job.id.startswith('flux_update_'):
                # Extraire l'ID du flux si c'est un job spécifique
                flux_id = None
                flux_name = None
                
                if job.id.startswith('flux_update_flux_'):
                    try:
                        flux_id = int(job.id.replace('flux_update_flux_', ''))
                        flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
                        flux_name = flux.nom if flux else 'Flux inconnu'
                    except:
                        pass
                
                jobs_info.append({
                    'job_id': job.id,
                    'job_name': job.name,
                    'flux_id': flux_id,
                    'flux_name': flux_name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                    'is_paused': job.next_run_time is None
                })
        
        # Statistiques sur les dernières mises à jour
        recent_updates = self.db.query(
            FluxRss.id,
            FluxRss.nom,
            FluxRss.derniere_maj,
            FluxRss.frequence_maj_heures
        ).filter(
            FluxRss.est_actif == True,
            FluxRss.derniere_maj != None
        ).order_by(
            FluxRss.derniere_maj.desc()
        ).limit(10).all()
        
        return {
            'scheduler_running': self.scheduler.running,
            'total_jobs': len(jobs_info),
            'jobs': jobs_info,
            'recent_updates': [
                {
                    'flux_id': flux.id,
                    'flux_nom': flux.nom,
                    'derniere_maj': flux.derniere_maj.isoformat() if flux.derniere_maj else None,
                    'prochaine_maj': (flux.derniere_maj + timedelta(hours=flux.frequence_maj_heures)).isoformat() 
                                    if flux.derniere_maj else None
                }
                for flux in recent_updates
            ]
        }
    
    def pause_scheduled_updates(self) -> bool:
        """Mettre en pause toutes les mises à jour planifiées"""
        try:
            self.scheduler.pause()
            logger.info("Mises à jour planifiées mises en pause")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise en pause: {str(e)}")
            return False
    
    def resume_scheduled_updates(self) -> bool:
        """Reprendre les mises à jour planifiées"""
        try:
            self.scheduler.resume()
            logger.info("Mises à jour planifiées reprises")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la reprise: {str(e)}")
            return False
    
    def remove_flux_from_user(self, user_id: int, flux_id: int) -> bool:
        """Retirer un flux des catégories de l'utilisateur"""
        flux_cats = self.db.query(FluxCategorie).join(Categorie).filter(
            Categorie.utilisateur_id == user_id,
            FluxCategorie.flux_id == flux_id
        ).all()
        
        if flux_cats:
            for fc in flux_cats:
                self.db.delete(fc)
            self.db.commit()
            
            # Vérifier si le flux n'est plus utilisé par personne
            remaining = self.db.query(FluxCategorie).filter_by(flux_id=flux_id).count()
            if remaining == 0:
                # Optionnel : désactiver le flux s'il n'est plus utilisé
                flux = self.db.query(FluxRss).filter_by(id=flux_id).first()
                if flux:
                    flux.est_actif = False
                    self.db.commit()
                    
                    # Retirer de la planification
                    job_id = f'flux_update_flux_{flux_id}'
                    if self.scheduler.get_job(job_id):
                        self.scheduler.remove_job(job_id)
            
            return True
        
        return False
    
    # ==================== MÉTHODES PRIVÉES ====================
    
    def _init_scheduler(self):
        """Initialiser le scheduler si nécessaire"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler initialisé")
    
    def _scheduled_update_all_flux(self):
        """Méthode appelée par le scheduler pour mettre à jour tous les flux"""
        logger.info("Début de la mise à jour planifiée de tous les flux")
        
        try:
            results = self.update_all_flux()
            logger.info(f"Mise à jour planifiée terminée: {results}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour planifiée: {str(e)}")
    
    def _schedule_single_flux_update(self, flux: FluxRss) -> bool:
        """Planifier la mise à jour d'un flux individuel selon sa fréquence"""
        try:
            job_id = f'flux_update_flux_{flux.id}'
            
            # Supprimer le job existant s'il existe
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Ajouter le nouveau job
            self.scheduler.add_job(
                func=self.update_flux,
                args=[flux.id],
                trigger=IntervalTrigger(hours=flux.frequence_maj_heures),
                id=job_id,
                name=f'MAJ flux: {flux.nom}',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=3600
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la planification du flux {flux.id}: {str(e)}")
            return False
    
    def _create_match_snippet(self, article: Article, query: str, context_length: int = 150) -> Optional[str]:
        """Créer un extrait avec le contexte de la recherche"""
        if not query:
            return None
        
        # Chercher le terme dans le contenu ou le résumé
        text = article.resume or article.contenu or ""
        if not text:
            return None
        
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Trouver la position du terme
        pos = text_lower.find(query_lower)
        if pos == -1:
            # Si pas trouvé, retourner le début du texte
            return text[:context_length] + "..." if len(text) > context_length else text
        
        # Extraire le contexte autour du terme trouvé
        start = max(0, pos - context_length // 2)
        end = min(len(text), pos + len(query) + context_length // 2)
        
        snippet = text[start:end]
        
        # Ajouter des ellipses si nécessaire
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def _validate_url(self, url: str) -> bool:
        """Valider une URL"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False
    
    def _parse_feed(self, url: str) -> Optional[Dict[str, Any]]:
        """Parser un flux RSS"""
        try:
            feed = feedparser.parse(url)
            
            # Vérifier si le parsing a réussi
            if feed.bozo and feed.bozo_exception:
                logger.error(f"Erreur de parsing pour {url}: {feed.bozo_exception}")
                return None
            
            # Vérifier qu'on a bien un flux valide
            if not hasattr(feed, 'feed'):
                return None
            
            return {
                'title': feed.feed.get('title', ''),
                'description': feed.feed.get('description', ''),
                'link': feed.feed.get('link', ''),
                'language': feed.feed.get('language', ''),
                'updated': feed.feed.get('updated', '')
            }
        except Exception as e:
            logger.error(f"Erreur lors du parsing du flux {url}: {str(e)}")
            return None
    
    def _fetch_articles(self, flux: FluxRss) -> int:
        """Récupérer les articles d'un flux"""
        try:
            feed = feedparser.parse(flux.url)
            new_articles = 0
            
            for entry in feed.entries:
                # Générer un GUID unique
                guid = entry.get('id', entry.get('link', ''))
                if not guid:
                    # Créer un GUID basé sur le titre et la date
                    guid_content = f"{entry.get('title', '')}{entry.get('published', '')}{entry.get('link', '')}"
                    guid = hashlib.md5(guid_content.encode()).hexdigest()
                
                # Limiter la longueur du GUID
                guid = guid[:500]
                
                # Vérifier si l'article existe déjà
                existing = self.db.query(Article).filter_by(
                    flux_id=flux.id,
                    guid=guid
                ).first()
                
                if not existing:
                    # Parser la date de publication
                    publie_le = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            publie_le = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                        except:
                            publie_le = None
                    
                    # Si pas de date de publication, utiliser updated_parsed
                    if not publie_le and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        try:
                            publie_le = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                        except:
                            publie_le = None
                    
                    # Si toujours pas de date, utiliser la date actuelle
                    if not publie_le:
                        publie_le = datetime.utcnow()
                    
                    # Extraire le contenu
                    contenu = None
                    if hasattr(entry, 'content') and entry.content:
                        contenu = entry.content[0].get('value', '')
                    
                    # Créer l'article
                    article = Article(
                        flux_id=flux.id,
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
            
            if new_articles > 0:
                self.db.commit()
                logger.info(f"Ajout de {new_articles} nouveaux articles pour le flux {flux.id}")
            
            return new_articles
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des articles pour le flux {flux.id}: {str(e)}")
            self.db.rollback()
            return 0