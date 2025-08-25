from sqlalchemy import Column, DateTime, ForeignKeyConstraint, Integer, String, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Categorie(Base):
    __tablename__ = 'categorie'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_categorie_utilisateur'),
        PrimaryKeyConstraint('id', name='categorie_pkey'),
        UniqueConstraint('nom', 'utilisateur_id', name='unique_categorie_par_utilisateur'),
        Index('idx_categorie_utilisateur', 'utilisateur_id')
    )

    id = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    utilisateur_id = Column(Integer, nullable=False)
    couleur = Column(String(7), server_default=text("'#007bff'::character varying"))
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    utilisateur = relationship('Utilisateur', back_populates='categorie')
    flux_categorie = relationship('FluxCategorie', back_populates='categorie')

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

    id = Column(Integer, primary_key=True)
    flux_id = Column(Integer, nullable=False)
    categorie_id = Column(Integer, nullable=False)

    categorie = relationship('Categorie', back_populates='flux_categorie')
    flux = relationship('FluxRss', back_populates='flux_categorie')