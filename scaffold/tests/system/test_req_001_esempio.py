"""Test di sistema: uno per requisito, con il codice nel nome (HE-SOP-005 par. 3.2).
Provano il prodotto dall'esterno, come lo usa l'utilizzatore, sulle immagini della pipeline."""

import requests


def test_req_001_il_backend_risponde():
    assert requests.get("http://localhost:8000/health", timeout=5).status_code == 200
