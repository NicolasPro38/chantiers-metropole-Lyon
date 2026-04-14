from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

Base = declarative_base()

class Chantier(Base):
    __tablename__ = 'chantiers'

    gid = Column(Integer, primary_key=True)
    numero = Column(String(50))
    intervenant = Column(String(255))
    nature_chantier = Column(String(255))
    nature_travaux = Column(Text)
    etat = Column(String(50))
    date_debut = Column(Date)
    date_fin = Column(Date)
    mesures_police = Column(Text)
    adresse = Column(Text)
    commune = Column(String(255))
    code_insee = Column(Integer)
    contact_tel = Column(String(100))
    contact_mail = Column(String(255))
    contact_url = Column(Text)
    last_update = Column(DateTime(timezone=True))
    geom = Column(Geometry(geometry_type='MULTIPOLYGON', srid=4326))

def get_engine():
    return create_engine(config.DATABASE_URL)

def init_db():
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("Tables recréées avec succès.")

if __name__ == "__main__":
    init_db()
