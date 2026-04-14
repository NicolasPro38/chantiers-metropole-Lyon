import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chantiers")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
FLASK_ENV = os.getenv("FLASK_ENV", "development")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# API Data Grand Lyon
API_BASE = "https://data.grandlyon.com/geoserver/ogc/features/v1/collections"
LAYER_CHANTIERS = "metropole-de-lyon:lyv_lyvia.lyvchantier"
LAYER_HISTORIQUE = "metropole-de-lyon:lyv_lyvia.lyvhistorique"
