# 🚧 Carte des Chantiers – Métropole de Lyon

Application web interactive de visualisation des travaux engagés sur le territoire de la Métropole de Lyon, développée dans le cadre d'un portfolio de cartographie web.

![Métropole Grand Lyon](https://img.shields.io/badge/Données-Data%20Grand%20Lyon-C8102E) ![License](https://img.shields.io/badge/Licence-Open%20Data-green) ![Python](https://img.shields.io/badge/Python-3.9-blue) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791)

---

## 🗺️ Présentation

Cette application permet de consulter en temps quasi-réel les **1 400+ chantiers en cours** sur la Métropole de Lyon. Elle s'appuie sur les données ouvertes de [Data Grand Lyon](https://data.grandlyon.com) et les affiche sous forme de **polygones géoréférencés** représentant les emprises réelles des chantiers.

L'interface reprend la **charte graphique officielle de la Métropole Grand Lyon** (couleurs, typographie Barlow Condensed, logo).

---

## ✨ Fonctionnalités

### Carte interactive
- Affichage des **emprises réelles** des chantiers (polygones, pas des points)
- **Couleurs par état** : orange (Ouvert), rouge (Validé), gris (Terminé)
- Clic sur un chantier → fiche détail complète (intervenant, dates, nature des travaux, adresse...)
- Légende intégrée

### Filtres
- Par **commune** (59 communes de la Métropole)
- Par **état** (Ouvert / Validé / Terminé)
- Par **nature de chantier** (voirie, réseaux, espaces publics...)

### Recherche
- Barre de recherche par **adresse ou lieu** via le géocodeur Photon de Data Grand Lyon
- Centrage automatique de la carte sur le lieu recherché

### Statistiques
- Compteur total de chantiers
- **Top 15 communes** les plus touchées (graphique barres)
- **Répartition par type de travaux** (graphique donut)
- Compteurs Ouverts / Validés

### Plugin QGIS
- Chargement des chantiers directement depuis PostGIS dans QGIS
- Filtres commune et état
- Style catégorisé identique à l'appli web
- Identification des entités au clic (outil natif QGIS)

---

## 📊 Source des données

| Donnée | Source | Fréquence |
|--------|--------|-----------|
| Travaux en cours | [Data Grand Lyon – lyv_lyvia.lyvchantier](https://data.grandlyon.com) | Quotidienne |
| Historique travaux | Data Grand Lyon – lyv_lyvia.lyvhistorique | Hebdomadaire |
| Géocodage adresses | Photon Grand Lyon | Temps réel |

Les données sont sous **Licence Ouverte / Open Licence v2.0** (Etalab).

---

## 🖥️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python / Flask |
| Base de données | PostgreSQL + PostGIS |
| Cartographie web | Leaflet.js |
| Graphiques | Chart.js |
| SIG desktop | QGIS 4 + plugin Python |
| Ingestion données | Python / requests |
| Automatisation | cron |
| Serveur | Ubuntu 22.04 / Apache / Gunicorn |

---

## 📁 Structure du projet

```
chantiers-metropole-lyon/
├── app/
│   ├── __init__.py       # Factory Flask
│   ├── models.py         # Modèle SQLAlchemy/PostGIS
│   ├── routes.py         # API REST (chantiers, communes, stats)
│   └── ingestion.py      # Script d'ingestion API → PostGIS
├── static/
│   ├── css/style.css     # Charte graphique Métropole
│   └── js/map.js         # Carte Leaflet + interactions
├── templates/
│   └── index.html        # Interface principale
├── qgis_plugin/
│   └── chantiers_metropole/  # Plugin QGIS Python
├── cron_ingest.sh        # Script cron d'ingestion
├── run.py                # Point d'entrée Flask
├── config.py             # Configuration (variables d'environnement)
├── .env.example          # Template variables d'environnement
└── requirements.txt      # Dépendances Python
```

---

## ⚙️ Installation

Voir [INSTALL.md](INSTALL.md) pour les instructions détaillées.

---

## 👤 Auteur

**Nicolas Rey Romano** — Géographe / Cartographe / Géomaticien  
[LinkedIn](https://www.linkedin.com/in/nicolas-rey-5898b3116/) · [Portfolio](https://cartonicolasrey.duckdns.org/portfolio/)

---

## 📄 Licence

Code source sous licence MIT. Données sous Licence Ouverte v2.0 (Data Grand Lyon / Etalab).
