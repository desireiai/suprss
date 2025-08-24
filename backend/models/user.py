from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

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

    id = Column(Integer, primary_key=True)
    nom_utilisateur = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    mot_de_passe_hash = Column(String(255))
    prenom = Column(String(100))
    nom = Column(String(100))
    avatar_url = Column(Text)
    email_verifie = Column(Boolean, server_default=text('false'))
    token_verification_email = Column(String(255))
    email_verifie_le = Column(DateTime)
    token_reset_password = Column(String(255))
    token_reset_expire_le = Column(DateTime)
    fournisseur_oauth = Column(String(50))
    id_oauth = Column(String(100))
    est_actif = Column(Boolean, server_default=text('true'))
    mode_sombre = Column(Boolean, server_default=text('false'))
    taille_police = Column(String(20), server_default=text("'medium'::character varying"))
    derniere_connexion = Column(DateTime)
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    categorie = relationship('Categorie', back_populates='utilisateur')
    collection = relationship('Collection', back_populates='proprietaire')
    journal_export = relationship('JournalExport', back_populates='utilisateur')
    journal_import = relationship('JournalImport', back_populates='utilisateur')
    utilisateur_oauth = relationship('UtilisateurOauth', back_populates='utilisateur')
    collection_flux = relationship('CollectionFlux', back_populates='ajoute_par_utilisateur')
    commentaire_article = relationship('CommentaireArticle', back_populates='utilisateur')
    membre_collection = relationship('MembreCollection', back_populates='utilisateur')
    message_collection = relationship('MessageCollection', back_populates='utilisateur')
    statut_utilisateur_article = relationship('StatutUtilisateurArticle', back_populates='utilisateur')

class UtilisateurOauth(Base):
    __tablename__ = 'utilisateur_oauth'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_utilisateur_oauth_utilisateur'),
        PrimaryKeyConstraint('id', name='utilisateur_oauth_pkey'),
        UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
        UniqueConstraint('utilisateur_id', 'provider', name='uq_user_provider'),
        Index('idx_utilisateur_oauth_cree_le', 'cree_le'),
        Index('idx_utilisateur_oauth_provider', 'provider'),
        Index('idx_utilisateur_oauth_provider_user', 'provider', 'provider_user_id'),
        Index('idx_utilisateur_oauth_utilisateur', 'utilisateur_id')
    )

    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, nullable=False)
    provider = Column(String(50), nullable=False)
    provider_user_id = Column(String(255), nullable=False)
    cree_le = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    provider_email = Column(String(255))
    provider_username = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    derniere_utilisation = Column(DateTime)

    utilisateur = relationship('Utilisateur', back_populates='utilisateur_oauth')
