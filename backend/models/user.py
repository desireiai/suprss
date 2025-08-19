from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from .base import Base
from .category import Categorie
from .import_export import JournalImport, JournalExport
from .interaction import CommentaireArticle, MessageCollection, StatutUtilisateurArticle
from .collection import Collection, CollectionFlux, MembreCollection

class Utilisateur(Base):
    __tablename__ = 'utilisateur'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='utilisateur_pkey'),
        UniqueConstraint('email', name='utilisateur_email_key'),
        UniqueConstraint('nom_utilisateur', name='utilisateur_nom_utilisateur_key'),
        Index('idx_utilisateur_email', 'email'),
        Index('idx_utilisateur_nom_utilisateur', 'nom_utilisateur'),
        Index('idx_utilisateur_oauth', 'fournisseur_oauth', 'id_oauth'),
        Index('idx_utilisateur_token_reset', 'token_reset_password'),
        Index('idx_utilisateur_token_verification', 'token_verification_email'),
        {'comment': "Table des utilisateurs de l'application SUPRSS"}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_utilisateur: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255))
    mot_de_passe_hash: Mapped[Optional[str]] = mapped_column(String(255))
    prenom: Mapped[Optional[str]] = mapped_column(String(100))
    nom: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    email_verifie: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    token_verification_email: Mapped[Optional[str]] = mapped_column(String(255))
    email_verifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    token_reset_password: Mapped[Optional[str]] = mapped_column(String(255))
    token_reset_expire_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    fournisseur_oauth: Mapped[Optional[str]] = mapped_column(String(50))
    id_oauth: Mapped[Optional[str]] = mapped_column(String(100))
    est_actif: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))
    mode_sombre: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    taille_police: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'medium'::character varying"))
    derniere_connexion: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    categorie: Mapped[List['Categorie']] = relationship('Categorie', back_populates='utilisateur')
    collection: Mapped[List['Collection']] = relationship('Collection', back_populates='proprietaire')
    journal_export: Mapped[List['JournalExport']] = relationship('JournalExport', back_populates='utilisateur')
    journal_import: Mapped[List['JournalImport']] = relationship('JournalImport', back_populates='utilisateur')
    collection_flux: Mapped[List['CollectionFlux']] = relationship('CollectionFlux', back_populates='ajoute_par_utilisateur')
    commentaire_article: Mapped[List['CommentaireArticle']] = relationship('CommentaireArticle', back_populates='utilisateur')
    membre_collection: Mapped[List['MembreCollection']] = relationship('MembreCollection', back_populates='utilisateur')
    message_collection: Mapped[List['MessageCollection']] = relationship('MessageCollection', back_populates='utilisateur')
    statut_utilisateur_article: Mapped[List['StatutUtilisateurArticle']] = relationship('StatutUtilisateurArticle', back_populates='utilisateur')
    oauth_accounts = relationship("UtilisateurOAuth", back_populates="utilisateur", cascade="all, delete-orphan")

class UtilisateurOAuth(Base):
    """Modèle pour stocker les liaisons OAuth des utilisateurs"""
    
    __tablename__ = 'utilisateur_oauth'
    
    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, ForeignKey('utilisateur.id', ondelete='CASCADE'), nullable=False)
    
    # Informations du provider
    provider = Column(String(50), nullable=False)  # 'google', 'microsoft', 'github'
    provider_user_id = Column(String(255), nullable=False)  # ID unique chez le provider
    provider_email = Column(String(255))
    provider_username = Column(String(255))
    
    # Tokens (optionnels, pour refresh si nécessaire)
    access_token = Column(Text)  # Peut être long
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Métadonnées
    cree_le = Column(DateTime, default=datetime.utcnow, nullable=False)
    derniere_utilisation = Column(DateTime)
    
    # Relations
    utilisateur = relationship("Utilisateur", back_populates="oauth_accounts")
    
    # Contrainte d'unicité : un provider_user_id ne peut être lié qu'à un seul utilisateur
    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
        UniqueConstraint('utilisateur_id', 'provider', name='uq_user_provider'),  # Un seul compte par provider par utilisateur
    )
    
    def __repr__(self):
        return f"<UtilisateurOAuth(user_id={self.utilisateur_id}, provider={self.provider})>"


# Ajouter cette ligne dans la classe Utilisateur existante (dans les relations) :
