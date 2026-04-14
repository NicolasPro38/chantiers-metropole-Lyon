import requests
import json
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from app.models import Chantier, get_engine

API_URL = f"{config.API_BASE}/{config.LAYER_CHANTIERS}/items"

def fetch_all_chantiers():
    """Récupère tous les chantiers depuis l'API Data Grand Lyon (pagination)."""
    features = []
    limit = 100
    start = 0

    print("Récupération des chantiers depuis Data Grand Lyon...")
    while True:
        params = {
            "f": "application/json",
            "limit": limit,
            "startIndex": start
        }
        r = requests.get(API_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        batch = data.get("features", [])
        features.extend(batch)
        print(f"  {len(features)} / {data.get('numberMatched', '?')} chantiers récupérés...")
        if len(batch) < limit:
            break
        start += limit

    print(f"Total : {len(features)} chantiers récupérés.")
    return features

def parse_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except:
        return None

def ingest():
    """Ingère les chantiers dans PostGIS."""
    features = fetch_all_chantiers()
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Vider la table avant réingestion
        session.query(Chantier).delete()
        session.commit()
        print("Table vidée, réingestion en cours...")

        count = 0
        for f in features:
            props = f.get("properties", {})
            geom_raw = f.get("geometry")

            if not geom_raw:
                continue

            try:
                geom = from_shape(shape(geom_raw), srid=4326)
            except Exception as e:
                print(f"  Erreur géométrie sur {props.get('numero')}: {e}")
                continue

            chantier = Chantier(
                gid=props.get("gid"),
                numero=props.get("numero"),
                intervenant=props.get("intervenant"),
                nature_chantier=props.get("nature_chantier"),
                nature_travaux=props.get("nature_travaux"),
                etat=props.get("etat"),
                date_debut=parse_date(props.get("date_debut")),
                date_fin=parse_date(props.get("date_fin")),
                mesures_police=props.get("mesures_police"),
                adresse=props.get("adresse"),
                commune=props.get("commune"),
                code_insee=props.get("code_insee"),
                contact_tel=props.get("contact_tel"),
                contact_mail=props.get("contact_mail"),
                contact_url=props.get("contact_url"),
                last_update=props.get("last_update"),
                geom=geom
            )
            session.add(chantier)
            count += 1

        session.commit()
        print(f"Ingestion terminée : {count} chantiers insérés.")

    except Exception as e:
        session.rollback()
        print(f"Erreur lors de l'ingestion : {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    ingest()
