#!/bin/bash
cd /home/ubuntu/chantiers-metropole-lyon
source venv/bin/activate
python app/ingestion.py >> logs/ingestion.log 2>&1
