from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Collection(Base):
    __tablename__ = 'collection'
    __table_args__ = (
        ForeignKeyConstraint(['proprietaire_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_collection_proprietaire'),
        PrimaryKeyConstraint('id', name='collection_pkey'),
        Index('idx_collection_nom', 'nom'),
        Index('idx_collection_proprietaire', 'proprietaire_id'),
        {'comment': 'Collections de flux RSS (personnelles ou partagées)'}
    )

    id = Column(Integer, primary_key=True)
    nom = Column(String(255), nullable=False)
    proprietaire_id = Column(Integer, nullable=False)
    description = Column(Text)
    est_partagee = Column(Boolean, server_default=text('false'))
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    proprietaire = relationship('Utilisateur', back_populates='collection')
    collection_flux = relationship('CollectionFlux', back_populates='collection')
    commentaire_article = relationship('CommentaireArticle', back_populates='collection')
    membre_collection = relationship('MembreCollection', back_populates='collection')
    message_collection = relationship('MessageCollection', back_populates='collection')

class CollectionFlux(Base):
    __tablename__ = 'collection_flux'
    __table_args__ = (
        ForeignKeyConstraint(['ajoute_par_utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_collection_flux_utilisateur'),
        ForeignKeyConstraint(['collection_id'], ['collection.id'], ondelete='CASCADE', name='fk_collection_flux_collection'),
        ForeignKeyConstraint(['flux_id'], ['flux_rss.id'], ondelete='CASCADE', name='fk_collection_flux_flux'),
        PrimaryKeyConstraint('id', name='collection_flux_pkey'),
        UniqueConstraint('collection_id', 'flux_id', name='unique_flux_par_collection'),
        Index('idx_collection_flux_collection', 'collection_id'),
        Index('idx_collection_flux_flux', 'flux_id')
    )

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, nullable=False)
    flux_id = Column(Integer, nullable=False)
    ajoute_par_utilisateur_id = Column(Integer, nullable=False)
    ajoute_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    ajoute_par_utilisateur = relationship('Utilisateur', back_populates='collection_flux')
    collection = relationship('Collection', back_populates='collection_flux')
    flux = relationship('FluxRss', back_populates='collection_flux')

class MembreCollection(Base):
    __tablename__ = 'membre_collection'
    __table_args__ = (
        ForeignKeyConstraint(['collection_id'], ['collection.id'], ondelete='CASCADE', name='fk_membre_collection_collection'),
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_membre_collection_utilisateur'),
        PrimaryKeyConstraint('id', name='membre_collection_pkey'),
        UniqueConstraint('collection_id', 'utilisateur_id', name='unique_membre_collection'),
        Index('idx_membre_collection_collection', 'collection_id'),
        Index('idx_membre_collection_utilisateur', 'utilisateur_id'),
        {'comment': 'Membres des collections avec leurs permissions'}
    )

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, nullable=False)
    utilisateur_id = Column(Integer, nullable=False)
    role = Column(Enum('proprietaire', 'administrateur', 'moderateur', 'membre', name='role_membre'), server_default=text("'membre'::role_membre"))
    peut_ajouter_flux = Column(Boolean, server_default=text('true'))
    peut_lire = Column(Boolean, server_default=text('true'))
    peut_commenter = Column(Boolean, server_default=text('true'))
    peut_modifier = Column(Boolean, server_default=text('false'))
    peut_supprimer = Column(Boolean, server_default=text('false'))
    rejoint_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    collection = relationship('Collection', back_populates='membre_collection')
    utilisateur = relationship('Utilisateur', back_populates='membre_collection')