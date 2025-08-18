from typing import List, Optional
from sqlalchemy import Column, DateTime, ForeignKeyConstraint, Integer, String, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from .base import Base
from .user import Utilisateur
from .rss import FluxRss

class Categorie(Base):
    __tablename__ = 'categorie'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_categorie_utilisateur'),
        PrimaryKeyConstraint('id', name='categorie_pkey'),
        UniqueConstraint('nom', 'utilisateur_id', name='unique_categorie_par_utilisateur'),
        Index('idx_categorie_utilisateur', 'utilisateur_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    couleur: Mapped[Optional[str]] = mapped_column(String(7), server_default=text("'#007bff'::character varying"))
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='categorie')
    flux_categorie: Mapped[List['FluxCategorie']] = relationship('FluxCategorie', back_populates='categorie')


class FluxCategorie(Base):
    __tablename__ = 'flux_categorie'
    __table_args__ = (
        ForeignKeyConstraint(['categorie_id'], ['categorie.id'], ondelete='CASCADE', name='fk_flux_categorie_categorie'),
        ForeignKeyConstraint(['flux_id'], ['flux_rss.id'], ondelete='CASCADE', name='fk_flux_categorie_flux'),
        PrimaryKeyConstraint('id', name='flux_categorie_pkey'),
        UniqueConstraint('flux_id', 'categorie_id', name='unique_flux_categorie'),
        Index('idx_flux_categorie_categorie', 'categorie_id'),
        Index('idx_flux_categorie_flux', 'flux_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flux_id: Mapped[int] = mapped_column(Integer)
    categorie_id: Mapped[int] = mapped_column(Integer)

    categorie: Mapped['Categorie'] = relationship('Categorie', back_populates='flux_categorie')
    flux: Mapped['FluxRss'] = relationship('FluxRss', back_populates='flux_categorie')