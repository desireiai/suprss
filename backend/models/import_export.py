from typing import Optional
from sqlalchemy import Column, DateTime, Enum, ForeignKeyConstraint, Integer, String, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from .base import Base
from .user import Utilisateur

class JournalImport(Base):
    __tablename__ = 'journal_import'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_import_utilisateur'),
        PrimaryKeyConstraint('id', name='journal_import_pkey'),
        Index('idx_import_cree_le', 'cree_le'),
        Index('idx_import_utilisateur', 'utilisateur_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(Enum('OPML', 'JSON', 'CSV', name='format_export_import'))
    nom_fichier: Mapped[str] = mapped_column(String(255))
    flux_importes: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='journal_import')

class JournalExport(Base):
    __tablename__ = 'journal_export'
    __table_args__ = (
        ForeignKeyConstraint(['utilisateur_id'], ['utilisateur.id'], ondelete='CASCADE', name='fk_export_utilisateur'),
        PrimaryKeyConstraint('id', name='journal_export_pkey'),
        Index('idx_export_cree_le', 'cree_le'),
        Index('idx_export_utilisateur', 'utilisateur_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(Enum('OPML', 'JSON', 'CSV', name='format_export_import'))
    nom_fichier: Mapped[str] = mapped_column(String(255))
    cree_le: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    utilisateur: Mapped['Utilisateur'] = relationship('Utilisateur', back_populates='journal_export')
