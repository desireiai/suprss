import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKeyConstraint, Index, Integer, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


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


vue_articles_utilisateur = Table(
    'vue_articles_utilisateur', Base.metadata,
    Column('id', Integer),
    Column('titre', String(500)),
    Column('lien', Text),
    Column('auteur', String(255)),
    Column('resume', Text),
    Column('publie_le', DateTime),
    Column('nom_flux', String(255)),
    Column('flux_id', Integer),
    Column('est_lu', Boolean),
    Column('est_favori', Boolean),
    Column('lu_le', DateTime),
    Column('mis_en_favori_le', DateTime),
    Column('utilisateur_id', Integer)
)


vue_collections_detaillees = Table(
    'vue_collections_detaillees', Base.metadata,
    Column('id', Integer),
    Column('nom', String(255)),
    Column('description', Text),
    Column('est_partagee', Boolean),
    Column('cree_le', DateTime),
    Column('proprietaire', String(50)),
    Column('nombre_flux', BigInteger),
    Column('nombre_membres', BigInteger)
)


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


class JournalExport(Base):
    __tablename__ = 'journal_export'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_export_utilisateur'),
        PrimaryKeyConstraint('id', name='journal_export_pkey'),
        Index('idx_export_cree_le', 'cree_le'),
        Index('idx_export_utilisateur', 'utilisateur_id')
    )

    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, nullable=False)
    format = Column(Enum('OPML', 'JSON', 'CSV', name='format_export_import'), nullable=False)
    nom_fichier = Column(String(255), nullable=False)
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    utilisateur = relationship('Utilisateur', back_populates='journal_export')


class JournalImport(Base):
    __tablename__ = 'journal_import'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_import_utilisateur'),
        PrimaryKeyConstraint('id', name='journal_import_pkey'),
        Index('idx_import_cree_le', 'cree_le'),
        Index('idx_import_utilisateur', 'utilisateur_id')
    )

    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, nullable=False)
    format = Column(Enum('OPML', 'JSON', 'CSV', name='format_export_import'), nullable=False)
    nom_fichier = Column(String(255), nullable=False)
    flux_importes = Column(Integer, server_default=text('0'))
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    utilisateur = relationship('Utilisateur', back_populates='journal_import')


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


class CommentaireArticle(Base):
    __tablename__ = 'commentaire_article'
    __table_args__ = (
        ForeignKeyConstraint(['article_id'], ['article.id'], ondelete='CASCADE', name='fk_commentaire_article'),
        ForeignKeyConstraint(['collection_id'], ['collection.id'], ondelete='CASCADE', name='fk_commentaire_collection'),
        ForeignKeyConstraint(['commentaire_parent_id'], ['commentaire_article.id'], ondelete='CASCADE', name='fk_commentaire_parent'),
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_commentaire_utilisateur'),
        PrimaryKeyConstraint('id', name='commentaire_article_pkey'),
        Index('idx_commentaire_article', 'article_id'),
        Index('idx_commentaire_collection', 'collection_id'),
        Index('idx_commentaire_cree_le', 'cree_le'),
        Index('idx_commentaire_parent', 'commentaire_parent_id'),
        Index('idx_commentaire_utilisateur', 'utilisateur_id'),
        {'comment': 'Commentaires sur les articles dans les collections partagées'}
    )

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, nullable=False)
    utilisateur_id = Column(Integer, nullable=False)
    collection_id = Column(Integer, nullable=False)
    contenu = Column(Text, nullable=False)
    commentaire_parent_id = Column(Integer)
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    article = relationship('Article', back_populates='commentaire_article')
    collection = relationship('Collection', back_populates='commentaire_article')
    commentaire_parent = relationship('CommentaireArticle', remote_side=[id], back_populates='commentaire_parent_reverse')
    commentaire_parent_reverse = relationship('CommentaireArticle', remote_side=[commentaire_parent_id], back_populates='commentaire_parent')
    utilisateur = relationship('Utilisateur', back_populates='commentaire_article')


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


class MessageCollection(Base):
    __tablename__ = 'message_collection'
    __table_args__ = (
        ForeignKeyConstraint(['collection_id'], ['collection.id'], ondelete='CASCADE', name='fk_message_collection'),
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_message_utilisateur'),
        PrimaryKeyConstraint('id', name='message_collection_pkey'),
        Index('idx_message_collection', 'collection_id'),
        Index('idx_message_cree_le', 'cree_le'),
        Index('idx_message_utilisateur', 'utilisateur_id'),
        {'comment': 'Messages de chat dans les collections partagées'}
    )

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, nullable=False)
    utilisateur_id = Column(Integer, nullable=False)
    contenu = Column(Text, nullable=False)
    cree_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    collection = relationship('Collection', back_populates='message_collection')
    utilisateur = relationship('Utilisateur', back_populates='message_collection')


class StatutUtilisateurArticle(Base):
    __tablename__ = 'statut_utilisateur_article'
    __table_args__ = (
        ForeignKeyConstraint(['article_id'], ['article.id'], ondelete='CASCADE', name='fk_statut_article'),
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_statut_utilisateur'),
        PrimaryKeyConstraint('id', name='statut_utilisateur_article_pkey'),
        UniqueConstraint('utilisateur_id', 'article_id', name='unique_statut_utilisateur_article'),
        Index('idx_statut_article', 'article_id'),
        Index('idx_statut_est_favori', 'est_favori'),
        Index('idx_statut_est_lu', 'est_lu'),
        Index('idx_statut_utilisateur', 'utilisateur_id'),
        {'comment': 'Statut de lecture et favoris par utilisateur'}
    )

    id = Column(Integer, primary_key=True)
    utilisateur_id = Column(Integer, nullable=False)
    article_id = Column(Integer, nullable=False)
    est_lu = Column(Boolean, server_default=text('false'))
    est_favori = Column(Boolean, server_default=text('false'))
    lu_le = Column(DateTime)
    mis_en_favori_le = Column(DateTime)

    article = relationship('Article', back_populates='statut_utilisateur_article')
    utilisateur = relationship('Utilisateur', back_populates='statut_utilisateur_article')