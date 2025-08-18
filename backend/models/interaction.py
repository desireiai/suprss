from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKeyConstraint, Integer, Text, UniqueConstraint, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from .base import Base
from .user import Utilisateur
from .rss import Article
from .collection import Collection

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    collection_id: Mapped[int] = mapped_column(Integer)
    contenu: Mapped[str] = mapped_column(Text)
    commentaire_parent_id: Mapped[Optional[int]] = mapped_column(Integer)
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    article: Mapped['Article'] = relationship('Article', back_populates='commentaire_article')
    collection: Mapped['Collection'] = relationship('Collection', back_populates='commentaire_article')
    commentaire_parent: Mapped[Optional['CommentaireArticle']] = relationship('CommentaireArticle', remote_side=[id], back_populates='commentaire_parent_reverse')
    commentaire_parent_reverse: Mapped[List['CommentaireArticle']] = relationship('CommentaireArticle', remote_side=[commentaire_parent_id], back_populates='commentaire_parent')
    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='commentaire_article')


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    collection_id: Mapped[int] = mapped_column(Integer)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    contenu: Mapped[str] = mapped_column(Text)
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    modifie_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    collection: Mapped['Collection'] = relationship('Collection', back_populates='message_collection')
    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='message_collection')


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    article_id: Mapped[int] = mapped_column(Integer)
    est_lu: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    est_favori: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    lu_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    mis_en_favori_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    article: Mapped['Article'] = relationship('Article', back_populates='statut_utilisateur_article')
    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='statut_utilisateur_article')
