from flask import Blueprint, jsonify, render_template, request
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, distinct
from geoalchemy2.functions import ST_AsGeoJSON
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from app.models import Chantier, get_engine

bp = Blueprint('main', __name__)

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/chantiers')
def api_chantiers():
    session = get_session()
    try:
        query = session.query(
            Chantier.gid,
            Chantier.numero,
            Chantier.intervenant,
            Chantier.nature_chantier,
            Chantier.nature_travaux,
            Chantier.etat,
            Chantier.date_debut,
            Chantier.date_fin,
            Chantier.mesures_police,
            Chantier.adresse,
            Chantier.commune,
            Chantier.code_insee,
            Chantier.contact_tel,
            Chantier.contact_mail,
            Chantier.contact_url,
            ST_AsGeoJSON(Chantier.geom).label('geojson')
        )

        # Filtres optionnels
        commune = request.args.get('commune')
        etat = request.args.get('etat')
        nature = request.args.get('nature_chantier')

        if commune:
            query = query.filter(Chantier.commune == commune)
        if etat:
            query = query.filter(Chantier.etat == etat)
        if nature:
            query = query.filter(Chantier.nature_chantier == nature)

        rows = query.all()

        features = []
        for row in rows:
            features.append({
                "type": "Feature",
                "geometry": json.loads(row.geojson),
                "properties": {
                    "gid": row.gid,
                    "numero": row.numero,
                    "intervenant": row.intervenant,
                    "nature_chantier": row.nature_chantier,
                    "nature_travaux": row.nature_travaux,
                    "etat": row.etat,
                    "date_debut": str(row.date_debut) if row.date_debut else None,
                    "date_fin": str(row.date_fin) if row.date_fin else None,
                    "mesures_police": row.mesures_police,
                    "adresse": row.adresse,
                    "commune": row.commune,
                    "contact_tel": row.contact_tel,
                    "contact_mail": row.contact_mail,
                    "contact_url": row.contact_url,
                }
            })

        return jsonify({
            "type": "FeatureCollection",
            "features": features,
            "total": len(features)
        })
    finally:
        session.close()

@bp.route('/api/communes')
def api_communes():
    session = get_session()
    try:
        rows = session.query(
            Chantier.commune,
            func.count(Chantier.gid).label('nb')
        ).group_by(Chantier.commune).order_by(Chantier.commune).all()

        return jsonify([{"commune": r.commune, "nb": r.nb} for r in rows])
    finally:
        session.close()

@bp.route('/api/stats')
def api_stats():
    session = get_session()
    try:
        # Stats par commune
        par_commune = session.query(
            Chantier.commune,
            func.count(Chantier.gid).label('nb')
        ).group_by(Chantier.commune).order_by(func.count(Chantier.gid).desc()).limit(15).all()

        # Stats par nature de chantier
        par_nature = session.query(
            Chantier.nature_chantier,
            func.count(Chantier.gid).label('nb')
        ).group_by(Chantier.nature_chantier).order_by(func.count(Chantier.gid).desc()).all()

        # Stats par état
        par_etat = session.query(
            Chantier.etat,
            func.count(Chantier.gid).label('nb')
        ).group_by(Chantier.etat).all()

        return jsonify({
            "par_commune": [{"label": r.commune, "nb": r.nb} for r in par_commune],
            "par_nature": [{"label": r.nature_chantier, "nb": r.nb} for r in par_nature],
            "par_etat": [{"label": r.etat, "nb": r.nb} for r in par_etat],
        })
    finally:
        session.close()
