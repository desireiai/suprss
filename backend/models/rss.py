from typing import List, Optional
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from .base import Base
from .interaction import CommentaireArticle, StatutUtilisateurArticle    
from .collection import CollectionFlux
from .category import FluxCategorie

class FluxRss(Base):
    __tablename__ = 'flux_rss'
    __table_args__ = (
        CheckConstraint('frequence_maj_heures > 0', name='flux_rss_frequence_maj_heures_check'),
        PrimaryKeyConstraint('id', name='flux_rss_pkey'),
        UniqueConstraint('url', name='flux_rss_url_key'),
        Index('idx_flux_rss_actif', 'est_actif'),
        Index('idx_flux_rss_derniere_maj', 'derniere_maj'),
        Index('idx_flux_rss_url', 'url'),
        {'comment': "Flux RSS configurés dans l'application"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    frequence_maj_heures: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('24'))
    est_actif: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    derniere_maj: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    article: Mapped[List['Article']] = relationship('Article', back_populates='flux')
    collection_flux: Mapped[List['CollectionFlux']] = relationship('CollectionFlux', back_populates='flux')
    flux_categorie: Mapped[List['FluxCategorie']] = relationship('FluxCategorie', back_populates='flux')

class Article(Base):
    __tablename__ = 'article'
    __table_args__ = (
        ForeignKeyConstraint(['flux_id'], ['flux_rss.id'], ondelete='CASCADE', name='fk_article_flux'),
        PrimaryKeyConstraint('id', name='article_pkey'),
        UniqueConstraint('guid', 'flux_id', name='unique_guid_par_flux'),
        Index('idx_article_contenu'),
        Index('idx_article_flux', 'flux_id'),
        Index('idx_article_guid', 'guid'),
        Index('idx_article_publie_le', 'publie_le'),
        Index('idx_article_titre'),
        {'comment': 'Articles récupérés depuis les flux RSS'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flux_id: Mapped[int] = mapped_column(Integer)
    titre: Mapped[str] = mapped_column(String(500))
    lien: Mapped[str] = mapped_column(Text)
    guid: Mapped[str] = mapped_column(String(500))
    auteur: Mapped[Optional[str]] = mapped_column(String(255))
    contenu: Mapped[Optional[str]] = mapped_column(Text)
    resume: Mapped[Optional[str]] = mapped_column(Text)
    publie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    recupere_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    flux: Mapped['FluxRss'] = relationship('FluxRss', back_populates='article')
    commentaire_article: Mapped[List['CommentaireArticle']] = relationship('CommentaireArticle', back_populates='article')
    statut_utilisateur_article: Mapped[List['StatutUtilisateurArticle']] = relationship('StatutUtilisateurArticle', back_populates='article')
