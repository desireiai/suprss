from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKeyConstraint, Integer, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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