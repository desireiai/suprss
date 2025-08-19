
# business/import_export_business.py
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import xml.etree.ElementTree as ET
import json
import csv
import io
import base64
from xml.dom import minidom

from ..models.user import Utilisateur
from ..models.rss import FluxRss, Article
from ..models.category import Categorie, FluxCategorie
from ..models.collection import Collection, CollectionFlux
from ..models.interaction import StatutUtilisateurArticle
from ..dto.import_export_dto import (
    ExportRequestDTO,
    ImportFileDTO,
    ImportResultDTO,
    ExportFormatEnum
)

class ImportExportBusiness:
    """Logique métier pour l'import/export des données"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_user_data(self, 
                        user_id: int,
                        request: ExportRequestDTO) -> Tuple[str, str, str]:
        """
        Exporter les données de l'utilisateur
        Retourne : (contenu, nom_fichier, content_type)
        """
        
        # Récupérer les données à exporter
        export_data = self._gather_export_data(user_id, request)
        
        # Générer le nom de fichier
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_filename = f"suprss_export_{timestamp}"
        
        # Exporter selon le format demandé
        if request.format == ExportFormatEnum.OPML:
            content = self._export_to_opml(export_data)
            filename = f"{base_filename}.opml"
            content_type = "application/xml"
            
        elif request.format == ExportFormatEnum.JSON:
            content = self._export_to_json(export_data)
            filename = f"{base_filename}.json"
            content_type = "application/json"
            
        elif request.format == ExportFormatEnum.CSV:
            content = self._export_to_csv(export_data)
            filename = f"{base_filename}.csv"
            content_type = "text/csv"
            
        else:
            raise ValueError(f"Format d'export non supporté: {request.format}")
        
        return content, filename, content_type
    
    def import_file(self, 
                   user_id: int,
                   import_dto: ImportFileDTO) -> ImportResultDTO:
        """Importer un fichier de flux RSS"""
        
        result = {
            'success': False,
            'imported_flux': 0,
            'skipped_flux': 0,
            'errors': [],
            'created_categories': [],
            'details': {}
        }
        
        try:
            # Décoder le contenu si nécessaire (base64)
            content = self._decode_content(import_dto.content)
            
            # Parser selon le format
            if import_dto.format == ExportFormatEnum.OPML:
                flux_data = self._parse_opml(content)
            elif import_dto.format == ExportFormatEnum.JSON:
                flux_data = self._parse_json(content)
            elif import_dto.format == ExportFormatEnum.CSV:
                flux_data = self._parse_csv(content)
            else:
                raise ValueError(f"Format d'import non supporté: {import_dto.format}")
            
            # Importer les flux
            for flux_item in flux_data:
                try:
                    imported = self._import_single_flux(
                        user_id, 
                        flux_item, 
                        import_dto.merge_strategy,
                        import_dto.default_category_id
                    )
                    
                    if imported:
                        result['imported_flux'] += 1
                        
                        # Créer la catégorie si nécessaire
                        if 'category' in flux_item and flux_item['category']:
                            if flux_item['category'] not in result['created_categories']:
                                cat_created = self._ensure_category_exists(
                                    user_id, 
                                    flux_item['category']
                                )
                                if cat_created:
                                    result['created_categories'].append(flux_item['category'])
                    else:
                        result['skipped_flux'] += 1
                        
                except Exception as e:
                    result['errors'].append(f"Erreur pour {flux_item.get('url', 'URL inconnue')}: {str(e)}")
                    result['skipped_flux'] += 1
            
            self.db.commit()
            result['success'] = result['imported_flux'] > 0
            
        except Exception as e:
            self.db.rollback()
            result['errors'].append(f"Erreur générale: {str(e)}")
        
        return ImportResultDTO(**result)
    
    # ==================== MÉTHODES D'EXPORT ====================
    
    def _gather_export_data(self, 
                           user_id: int,
                           request: ExportRequestDTO) -> Dict[str, Any]:
        """Rassembler toutes les données à exporter"""
        
        data = {
            'user': None,
            'categories': [],
            'flux': [],
            'collections': []
        }
        
        # Informations utilisateur
        user = self.db.query(Utilisateur).filter_by(id=user_id).first()
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        data['user'] = {
            'nom_utilisateur': user.nom_utilisateur,
            'email': user.email,
            'export_date': datetime.utcnow().isoformat()
        }
        
        # Catégories et flux personnels
        if request.include_categories or request.include_personal_flux:
            categories = self.db.query(Categorie).filter_by(
                utilisateur_id=user_id
            ).all()
            
            for cat in categories:
                category_data = {
                    'nom': cat.nom,
                    'couleur': cat.couleur,
                    'flux': []
                }
                
                if request.include_personal_flux:
                    # Récupérer les flux de cette catégorie
                    flux_cats = self.db.query(FluxCategorie).filter_by(
                        categorie_id=cat.id
                    ).all()
                    
                    for fc in flux_cats:
                        flux = fc.flux
                        flux_data = {
                            'nom': flux.nom,
                            'url': flux.url,
                            'description': flux.description,
                            'frequence_maj_heures': flux.frequence_maj_heures
                        }
                        
                        # Ajouter les statuts si demandé
                        if request.include_read_status or request.include_favorites:
                            flux_data['articles_status'] = self._get_articles_status(
                                user_id, 
                                flux.id,
                                request.include_read_status,
                                request.include_favorites
                            )
                        
                        category_data['flux'].append(flux_data)
                
                data['categories'].append(category_data)
        
        # Collections partagées (seulement celles créées par l'utilisateur)
        if request.include_collections:
            collections = self.db.query(Collection).filter_by(
                proprietaire_id=user_id
            ).all()
            
            for coll in collections:
                collection_data = {
                    'nom': coll.nom,
                    'description': coll.description,
                    'est_partagee': coll.est_partagee,
                    'flux': []
                }
                
                # Flux de la collection
                coll_flux = self.db.query(CollectionFlux).filter_by(
                    collection_id=coll.id
                ).all()
                
                for cf in coll_flux:
                    flux = cf.flux
                    collection_data['flux'].append({
                        'nom': flux.nom,
                        'url': flux.url,
                        'description': flux.description
                    })
                
                data['collections'].append(collection_data)
        
        return data
    
    def _export_to_opml(self, data: Dict[str, Any]) -> str:
        """Exporter en format OPML"""
        
        # Créer le document OPML
        opml = ET.Element('opml', version='2.0')
        
        # Head
        head = ET.SubElement(opml, 'head')
        ET.SubElement(head, 'title').text = f"SUPRSS Export - {data['user']['nom_utilisateur']}"
        ET.SubElement(head, 'dateCreated').text = data['user']['export_date']
        ET.SubElement(head, 'ownerName').text = data['user']['nom_utilisateur']
        ET.SubElement(head, 'ownerEmail').text = data['user']['email']
        
        # Body
        body = ET.SubElement(opml, 'body')
        
        # Ajouter les catégories et flux
        for category in data['categories']:
            if category['flux']:  # Seulement si la catégorie a des flux
                # Créer un outline pour la catégorie
                cat_outline = ET.SubElement(body, 'outline',
                    text=category['nom'],
                    title=category['nom']
                )
                
                # Ajouter les flux de la catégorie
                for flux in category['flux']:
                    ET.SubElement(cat_outline, 'outline',
                        type='rss',
                        text=flux['nom'],
                        title=flux['nom'],
                        xmlUrl=flux['url'],
                        htmlUrl=flux.get('url', ''),
                        description=flux.get('description', '')
                    )
            else:
                # Catégorie vide, on peut l'ajouter quand même
                ET.SubElement(body, 'outline',
                    text=category['nom'],
                    title=category['nom']
                )
        
        # Ajouter les collections
        if data['collections']:
            collections_outline = ET.SubElement(body, 'outline',
                text='Collections partagées',
                title='Collections partagées'
            )
            
            for collection in data['collections']:
                coll_outline = ET.SubElement(collections_outline, 'outline',
                    text=collection['nom'],
                    title=collection['nom'],
                    description=collection.get('description', '')
                )
                
                for flux in collection['flux']:
                    ET.SubElement(coll_outline, 'outline',
                        type='rss',
                        text=flux['nom'],
                        title=flux['nom'],
                        xmlUrl=flux['url'],
                        description=flux.get('description', '')
                    )
        
        # Convertir en string avec indentation
        rough_string = ET.tostring(opml, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _export_to_json(self, data: Dict[str, Any]) -> str:
        """Exporter en format JSON"""
        
        export = {
            'version': '1.0',
            'generator': 'SUPRSS',
            'export_date': data['user']['export_date'],
            'user': data['user'],
            'data': {
                'categories': [],
                'collections': []
            }
        }
        
        # Formater les catégories
        for category in data['categories']:
            cat_data = {
                'name': category['nom'],
                'color': category['couleur'],
                'feeds': []
            }
            
            for flux in category['flux']:
                feed_data = {
                    'name': flux['nom'],
                    'url': flux['url'],
                    'description': flux.get('description', ''),
                    'update_frequency_hours': flux.get('frequence_maj_heures', 6)
                }
                
                # Ajouter les statuts si présents
                if 'articles_status' in flux:
                    feed_data['articles_status'] = flux['articles_status']
                
                cat_data['feeds'].append(feed_data)
            
            export['data']['categories'].append(cat_data)
        
        # Formater les collections
        for collection in data['collections']:
            coll_data = {
                'name': collection['nom'],
                'description': collection.get('description', ''),
                'is_shared': collection['est_partagee'],
                'feeds': []
            }
            
            for flux in collection['flux']:
                coll_data['feeds'].append({
                    'name': flux['nom'],
                    'url': flux['url'],
                    'description': flux.get('description', '')
                })
            
            export['data']['collections'].append(coll_data)
        
        return json.dumps(export, indent=2, ensure_ascii=False)
    
    def _export_to_csv(self, data: Dict[str, Any]) -> str:
        """Exporter en format CSV"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        headers = [
            'Type',
            'Category/Collection',
            'Feed Name',
            'Feed URL',
            'Description',
            'Update Frequency (hours)',
            'Color'
        ]
        writer.writerow(headers)
        
        # Écrire les flux personnels par catégorie
        for category in data['categories']:
            for flux in category['flux']:
                writer.writerow([
                    'Personal',
                    category['nom'],
                    flux['nom'],
                    flux['url'],
                    flux.get('description', ''),
                    flux.get('frequence_maj_heures', 6),
                    category.get('couleur', '')
                ])
            
            # Ajouter une ligne pour les catégories vides
            if not category['flux']:
                writer.writerow([
                    'Personal',
                    category['nom'],
                    '',
                    '',
                    '',
                    '',
                    category.get('couleur', '')
                ])
        
        # Écrire les flux des collections
        for collection in data['collections']:
            for flux in collection['flux']:
                writer.writerow([
                    'Collection',
                    collection['nom'],
                    flux['nom'],
                    flux['url'],
                    flux.get('description', ''),
                    '',
                    ''
                ])
        
        return output.getvalue()
    
    # ==================== MÉTHODES D'IMPORT ====================
    
    def _parse_opml(self, content: str) -> List[Dict[str, Any]]:
        """Parser un fichier OPML"""
        
        flux_list = []
        
        try:
            root = ET.fromstring(content)
            body = root.find('body')
            
            if body is None:
                raise ValueError("OPML invalide: pas de body")
            
            # Parser récursivement les outlines
            for outline in body.findall('.//outline'):
                self._parse_opml_outline(outline, flux_list)
                
        except ET.ParseError as e:
            raise ValueError(f"Erreur de parsing OPML: {str(e)}")
        
        return flux_list
    
    def _parse_opml_outline(self, 
                           outline: ET.Element,
                           flux_list: List[Dict[str, Any]],
                           parent_category: Optional[str] = None):
        """Parser un outline OPML récursivement"""
        
        # Vérifier si c'est un flux RSS
        if outline.get('type') == 'rss' or outline.get('xmlUrl'):
            flux_data = {
                'nom': outline.get('text') or outline.get('title', 'Sans titre'),
                'url': outline.get('xmlUrl'),
                'description': outline.get('description', ''),
                'category': parent_category
            }
            
            if flux_data['url']:  # Seulement si on a une URL
                flux_list.append(flux_data)
        
        else:
            # C'est peut-être une catégorie
            category_name = outline.get('text') or outline.get('title')
            
            # Parser les enfants
            for child in outline.findall('outline'):
                self._parse_opml_outline(child, flux_list, category_name)
    
    def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """Parser un fichier JSON"""
        
        flux_list = []
        
        try:
            data = json.loads(content)
            
            # Support de différentes structures JSON
            if 'data' in data:
                # Format SUPRSS
                categories = data.get('data', {}).get('categories', [])
                collections = data.get('data', {}).get('collections', [])
                
                # Parser les catégories
                for category in categories:
                    category_name = category.get('name', 'Sans catégorie')
                    
                    for feed in category.get('feeds', []):
                        flux_list.append({
                            'nom': feed.get('name', feed.get('title', 'Sans titre')),
                            'url': feed.get('url', feed.get('xmlUrl', '')),
                            'description': feed.get('description', ''),
                            'category': category_name,
                            'frequence_maj_heures': feed.get('update_frequency_hours', 6)
                        })
                
                # Parser les collections
                for collection in collections:
                    for feed in collection.get('feeds', []):
                        flux_list.append({
                            'nom': feed.get('name', 'Sans titre'),
                            'url': feed.get('url', ''),
                            'description': feed.get('description', ''),
                            'category': f"Collection: {collection.get('name', 'Sans nom')}"
                        })
            
            elif isinstance(data, list):
                # Format simple : liste de flux
                for item in data:
                    if isinstance(item, dict) and 'url' in item:
                        flux_list.append({
                            'nom': item.get('name', item.get('title', 'Sans titre')),
                            'url': item['url'],
                            'description': item.get('description', ''),
                            'category': item.get('category')
                        })
            
            else:
                # Format plat
                if 'feeds' in data:
                    for feed in data['feeds']:
                        flux_list.append({
                            'nom': feed.get('name', 'Sans titre'),
                            'url': feed.get('url', ''),
                            'description': feed.get('description', ''),
                            'category': feed.get('category')
                        })
                        
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de parsing JSON: {str(e)}")
        
        return flux_list
    
    def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parser un fichier CSV"""
        
        flux_list = []
        
        try:
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                # Essayer différents formats de colonnes
                url = row.get('Feed URL') or row.get('URL') or row.get('url') or row.get('xmlUrl')
                
                if url and url.strip():  # Seulement si on a une URL
                    flux_list.append({
                        'nom': (row.get('Feed Name') or row.get('Name') or 
                               row.get('Title') or row.get('title') or 'Sans titre'),
                        'url': url.strip(),
                        'description': row.get('Description', ''),
                        'category': (row.get('Category/Collection') or 
                                   row.get('Category') or row.get('category')),
                        'frequence_maj_heures': int(row.get('Update Frequency (hours)', 6))
                                               if row.get('Update Frequency (hours)', '').isdigit() 
                                               else 6
                    })
                    
        except csv.Error as e:
            raise ValueError(f"Erreur de parsing CSV: {str(e)}")
        
        return flux_list
    
    def _import_single_flux(self,
                           user_id: int,
                           flux_data: Dict[str, Any],
                           merge_strategy: str,
                           default_category_id: Optional[int]) -> bool:
        """Importer un flux unique"""
        
        url = flux_data.get('url', '').strip()
        
        if not url:
            return False
        
        # Vérifier si le flux existe déjà
        existing_flux = self.db.query(FluxRss).filter_by(url=url).first()
        
        if existing_flux:
            if merge_strategy == 'skip':
                return False
            elif merge_strategy == 'replace':
                # Mettre à jour le flux existant
                existing_flux.nom = flux_data.get('nom', existing_flux.nom)
                existing_flux.description = flux_data.get('description', existing_flux.description)
                existing_flux.frequence_maj_heures = flux_data.get('frequence_maj_heures', 6)
        else:
            # Créer un nouveau flux
            existing_flux = FluxRss(
                nom=flux_data.get('nom', 'Flux importé'),
                url=url,
                description=flux_data.get('description', ''),
                frequence_maj_heures=flux_data.get('frequence_maj_heures', 6)
            )
            self.db.add(existing_flux)
            self.db.flush()
        
        # Gérer la catégorie
        category_id = default_category_id
        
        if flux_data.get('category'):
            # Chercher ou créer la catégorie
            category = self.db.query(Categorie).filter_by(
                utilisateur_id=user_id,
                nom=flux_data['category']
            ).first()
            
            if category:
                category_id = category.id
            else:
                # Créer la catégorie si elle n'existe pas
                category = Categorie(
                    nom=flux_data['category'],
                    utilisateur_id=user_id,
                    couleur='#007bff'
                )
                self.db.add(category)
                self.db.flush()
                category_id = category.id
        
        # Si pas de catégorie spécifiée, utiliser la catégorie par défaut
        if not category_id:
            default_cat = self.db.query(Categorie).filter_by(
                utilisateur_id=user_id,
                nom="Non classé"
            ).first()
            
            if default_cat:
                category_id = default_cat.id
        
        # Associer le flux à la catégorie
        if category_id:
            # Vérifier que l'association n'existe pas déjà
            existing_assoc = self.db.query(FluxCategorie).filter_by(
                flux_id=existing_flux.id,
                categorie_id=category_id
            ).first()
            
            if not existing_assoc:
                flux_cat = FluxCategorie(
                    flux_id=existing_flux.id,
                    categorie_id=category_id
                )
                self.db.add(flux_cat)
        
        return True
    
    def _ensure_category_exists(self, user_id: int, category_name: str) -> bool:
        """S'assurer qu'une catégorie existe, la créer si nécessaire"""
        
        if not category_name:
            return False
        
        category = self.db.query(Categorie).filter_by(
            utilisateur_id=user_id,
            nom=category_name
        ).first()
        
        if not category:
            category = Categorie(
                nom=category_name,
                utilisateur_id=user_id,
                couleur='#007bff'
            )
            self.db.add(category)
            self.db.flush()
            return True
        
        return False
    
    def _get_articles_status(self,
                            user_id: int,
                            flux_id: int,
                            include_read: bool,
                            include_favorites: bool) -> List[Dict[str, Any]]:
        """Récupérer les statuts des articles pour un flux"""
        
        statuses = []
        
        articles = self.db.query(Article).filter_by(flux_id=flux_id).all()
        
        for article in articles:
            statut = self.db.query(StatutUtilisateurArticle).filter_by(
                utilisateur_id=user_id,
                article_id=article.id
            ).first()
            
            if statut and (statut.est_lu or statut.est_favori):
                status_data = {
                    'article_guid': article.guid,
                    'article_title': article.titre
                }
                
                if include_read and statut.est_lu:
                    status_data['is_read'] = True
                    status_data['read_at'] = statut.lu_le.isoformat() if statut.lu_le else None
                
                if include_favorites and statut.est_favori:
                    status_data['is_favorite'] = True
                    status_data['favorited_at'] = statut.mis_en_favori_le.isoformat() if statut.mis_en_favori_le else None
                
                statuses.append(status_data)
        
        return statuses
    
    def _decode_content(self, content: str) -> str:
        """Décoder le contenu si nécessaire"""
        
        # Vérifier si c'est du base64
        try:
            # Tenter de décoder depuis base64
            decoded = base64.b64decode(content)
            return decoded.decode('utf-8')
        except:
            # Pas du base64, retourner tel quel
            return content