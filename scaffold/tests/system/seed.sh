#!/usr/bin/env bash
# Carica i dati sintetici nel prodotto avviato da compose.yaml (HE-SOP-005 par. 3.1: dati sintetici,
# mai dati di paziente). Eseguito da e2e dopo `docker compose up --wait`, prima di pytest.
set -euo pipefail
echo "nessun dato sintetico da caricare: compilare questo script quando il prodotto ne ha bisogno"
