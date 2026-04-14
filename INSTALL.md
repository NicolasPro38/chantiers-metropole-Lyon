# 📘 Documentation Technique – Carte des Chantiers Métropole de Lyon

## Architecture générale

```
API Data Grand Lyon (OGC Features)
         │
         ▼ (cron Python – quotidien)
  PostgreSQL / PostGIS
  table: chantiers (MultiPolygon, SRID 4326)
         │
         ├──▶ Flask API REST ──▶ Leaflet.js (appli web)
         │
         └──▶ Plugin QGIS Python (SIG desktop)
```

---

## Prérequis

- Python 3.9+
- PostgreSQL 14+ avec extension PostGIS
- QGIS 3.16+ (pour le plugin)

---

## Installation locale

### 1. Cloner le repo

```bash
git clone https://github.com/NicolasPro38/chantiers-metropole-Lyon.git
cd chantiers-metropole-Lyon
```

### 2. Environnement virtuel et dépendances

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

```env
DB_HOST=localhost
DB_NAME=chantiers
DB_USER=user_chantiers
DB_PASSWORD=votre_mot_de_passe
SECRET_KEY=votre_clé_secrète
FLASK_ENV=development
```

### 4. Base de données PostGIS

```sql
CREATE DATABASE chantiers;
\c chantiers
CREATE EXTENSION postgis;
CREATE USER user_chantiers WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE chantiers TO user_chantiers;
GRANT ALL ON SCHEMA public TO user_chantiers;
```

### 5. Créer les tables et ingérer les données

```bash
python app/models.py
python app/ingestion.py
```

### 6. Lancer l'application

```bash
python run.py
# → http://127.0.0.1:5004
```

---

## API Data Grand Lyon

L'application consomme l'**API OGC Features** de Data Grand Lyon :

| Endpoint | Description |
|----------|-------------|
| `metropole-de-lyon:lyv_lyvia.lyvchantier` | Chantiers en cours |
| `metropole-de-lyon:lyv_lyvia.lyvhistorique` | Historique depuis 2013 |

Paramètres : `f=application/json`, `limit=100`, `startIndex=N` (pagination automatique).  
Géométrie : **MultiPolygon**, EPSG:4326.

---

## Modèle de données PostGIS

```sql
CREATE TABLE chantiers (
    gid             INTEGER PRIMARY KEY,
    numero          VARCHAR(50),
    intervenant     VARCHAR(255),
    nature_chantier VARCHAR(255),
    nature_travaux  TEXT,
    etat            VARCHAR(50),
    date_debut      DATE,
    date_fin        DATE,
    mesures_police  TEXT,
    adresse         TEXT,
    commune         VARCHAR(255),
    code_insee      INTEGER,
    contact_tel     VARCHAR(100),
    contact_mail    VARCHAR(255),
    contact_url     TEXT,
    last_update     TIMESTAMPTZ,
    geom            GEOMETRY(MULTIPOLYGON, 4326)
);
```

---

## API Flask

| Route | Méthode | Paramètres | Description |
|-------|---------|------------|-------------|
| `/` | GET | – | Interface carte |
| `/api/chantiers` | GET | `commune`, `etat`, `nature_chantier` | GeoJSON filtré |
| `/api/communes` | GET | – | Liste communes + compteurs |
| `/api/stats` | GET | – | Stats par commune, nature, état |

---

## Ingestion automatique (cron)

```bash
crontab -e
# Ajouter :
0 3 * * * /home/ubuntu/chantiers-metropole-lyon/cron_ingest.sh
```

Les logs sont écrits dans `logs/ingestion.log`.

---

## Déploiement VPS (Ubuntu 22.04)

### Service systemd

```ini
[Unit]
Description=Chantiers Métropole de Lyon
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/chantiers-metropole-lyon
Environment="PATH=/home/ubuntu/chantiers-metropole-lyon/venv/bin"
ExecStart=/home/ubuntu/chantiers-metropole-lyon/venv/bin/gunicorn -w 2 -b 127.0.0.1:5005 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

### Reverse proxy Apache

```apache
ProxyPass /chantiers/ http://127.0.0.1:5005/
ProxyPassReverse /chantiers/ http://127.0.0.1:5005/
```

---

## Plugin QGIS

### Installation

Copier `qgis_plugin/chantiers_metropole/` dans :
- **Mac** : `~/Library/Application Support/QGIS/QGIS4/profiles/default/python/plugins/`
- **Linux** : `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
- **Windows** : `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`

### Utilisation

1. Activer dans **Extensions → Installer/Gérer les extensions**
2. Menu **Métropole de Lyon → 🚧 Chantiers Métropole de Lyon**
3. Sélectionner les filtres et cliquer **Charger la couche**
4. Outil **Identifier** (touche `I`) pour consulter les attributs

---

## Auteur

**Nicolas Rey Romano** — Géographe / Cartographe / Géomaticien  
[LinkedIn](https://www.linkedin.com/in/nicolas-rey-5898b3116/)
