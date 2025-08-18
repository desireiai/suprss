from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from .base import Base
from .user import Utilisateur
from .rss import FluxRss
from .interaction import CommentaireArticle, MessageCollection

class Collection(Base):
    __tablename__ = 'collection'
    __table_args__ = (
        ForeignKeyConstraint(['proprietaire_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_collection_proprietaire'),
        PrimaryKeyConstraint('id', name='collection_pkey'),
        Index('idx_collection_nom', 'nom'),
        Index('idx_collection_proprietaire', 'proprietaire_id'),
        {'comment': 'Collections de flux RSS (personnelles ou partagées)'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(255))
    proprietaire_id: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    est_partagee: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    proprietaire: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='collection')
    collection_flux: Mapped[List['CollectionFlux']] = relationship('CollectionFlux', back_populates='collection')
    commentaire_article: Mapped[List['CommentaireArticle']] = relationship('CommentaireArticle', back_populates='collection')
    membre_collection: Mapped[List['MembreCollection']] = relationship('MembreCollection', back_populates='collection')
    message_collection: Mapped[List['MessageCollection']] = relationship('MessageCollection', back_populates='collection')

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(Integer)
    flux_id: Mapped[int] = mapped_column(Integer)
    ajoute_par_utilisateur_id: Mapped[int] = mapped_column(Integer)
    ajoute_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    ajoute_par_utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='collection_flux')
    collection: Mapped['Collection'] = relationship('Collection', back_populates='collection_flux')
    flux: Mapped['FluxRss'] = relationship('FluxRss', back_populates='collection_flux')

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(Integer)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[Optional[str]] = mapped_column(Enum('proprietaire', 'administrateur', 'moderateur', 'membre', name='role_membre'), server_default=text("'membre'::role_membre"))
    peut_ajouter_flux: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    peut_lire: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    peut_commenter: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    peut_modifier: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    peut_supprimer: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    rejoint_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    collection: Mapped['Collection'] = relationship('Collection', back_populates='membre_collection')
    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='membre_collection')