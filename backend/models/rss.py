from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
import datetime
from .base import Base

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

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text)
    frequence_maj_heures = Column(Integer, server_default=text('24'))
    est_actif = Column(Boolean, server_default=text('true'))
    derniere_maj = Column(DateTime)
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    article = relationship('Article', back_populates='flux')
    collection_flux = relationship('CollectionFlux', back_populates='flux')
    flux_categorie = relationship('FluxCategorie', back_populates='flux')

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

    id = Column(Integer, primary_key=True)
    flux_id = Column(Integer, nullable=False)
    titre = Column(String(500), nullable=False)
    lien = Column(Text, nullable=False)
    guid = Column(String(500), nullable=False)
    auteur = Column(String(255))
    contenu = Column(Text)
    resume = Column(Text)
    publie_le = Column(DateTime)
    recupere_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    flux = relationship('FluxRss', back_populates='article')
    commentaire_article = relationship('CommentaireArticle', back_populates='article')
    statut_utilisateur_article = relationship('StatutUtilisateurArticle', back_populates='article')