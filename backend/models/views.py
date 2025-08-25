from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Table, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

t_vue_articles_utilisateur = Table(
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

t_vue_collections_detaillees = Table(
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