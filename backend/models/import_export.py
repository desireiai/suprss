from typing import Optional
from sqlalchemy import Column, DateTime, Enum, ForeignKeyConstraint, Integer, String, Index, text, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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