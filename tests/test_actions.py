"""Test delle action: le parti deterministiche che non chiamano GitHub, Linear o l'LLM."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "actions" / "_lib"))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "actions" / name / "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


soup = load("soup-evidence")
trace = load("traceability")
draft = load("draft-docs")


def test_dockerfile_bases(tmp_path):
    (tmp_path / "Dockerfile").write_text(
        "FROM node:24@sha256:aaa AS build\nFROM nginxinc/nginx-unprivileged:1.30-alpine@sha256:bbb\nFROM build\n"
    )
    bases = soup.dockerfile_bases(tmp_path / "Dockerfile")
    assert bases == [
        {"componente": "node", "produttore": "library", "versione": "24@sha256:aaa", "tipo": "immagine"},
        {
            "componente": "nginx-unprivileged",
            "produttore": "nginxinc",
            "versione": "1.30-alpine@sha256:bbb",
            "tipo": "immagine",
        },
    ]


def test_python_deps(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\nNumPy >= 2\n# commento\n-r other.txt\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = ["pandas==2.3.2", "Bambi"]\n')
    sbom = {("pypi", "numpy"): ("2.3.3", "NumPy developers"), ("pypi", "bambi"): ("0.21.0", "")}
    deps = soup.python_deps(tmp_path, sbom)
    assert {d["componente"]: d["versione"] for d in deps} == {
        "fastapi": "0.115.0",
        "numpy": "2.3.3",
        "pandas": "2.3.2",
        "bambi": "0.21.0",
    }
    assert next(d for d in deps if d["componente"] == "numpy")["produttore"] == "NumPy developers"


def test_node_deps(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"react": "^19.3.0"}, "devDependencies": {"vitest": "^3"}})
    )
    (tmp_path / "package-lock.json").write_text(json.dumps({"packages": {"node_modules/react": {"version": "19.3.1"}}}))
    deps = soup.node_deps(tmp_path, {("npm", "react"): ("19.3.1", "Meta Open Source")})
    assert deps == [{"componente": "react", "produttore": "Meta Open Source", "versione": "19.3.1", "tipo": "npm"}]


def test_norm_key_e_segnaposto():
    assert soup.norm_key("python (immagine python:3.12-slim)") == "python"
    assert soup.norm_key("React_DOM") == "react-dom"
    assert soup.is_placeholder({"versione": "DA DEFINIRE", "funzione_nel_prodotto": "x"})
    assert soup.is_placeholder({"versione": "", "funzione_nel_prodotto": ""})
    assert soup.is_placeholder({"versione": "x", "funzione_nel_prodotto": "NON E' SOUP alla data"})
    assert not soup.is_placeholder({"versione": "2.3.3", "funzione_nel_prodotto": "calcolo"})


def test_sbom_index(tmp_path):
    doc = {
        "packages": [
            {
                "name": "NumPy",
                "versionInfo": "2.3.3",
                "supplier": "Organization: NumPy developers",
                "externalRefs": [{"referenceType": "purl", "referenceLocator": "pkg:pypi/numpy@2.3.3"}],
            },
            {
                "name": "react",
                "versionInfo": "19.3.1",
                "supplier": "NOASSERTION",
                "externalRefs": [{"referenceType": "purl", "referenceLocator": "pkg:npm/react@19.3.1"}],
            },
        ]
    }
    (tmp_path / "sbom-backend.spdx.json").write_text(json.dumps(doc))
    idx = soup.sbom_index(tmp_path, "backend")
    assert idx[("pypi", "numpy")] == ("2.3.3", "NumPy developers") and idx[("npm", "react")] == ("19.3.1", "")


def test_previous_tag(tmp_path):
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "a"],
        cwd=tmp_path,
        check=True,
    )
    for t in ("so-v1.0.0", "so-v1.2.0", "so-v1.10.0", "altro-v9.0.0"):
        subprocess.run(["git", "tag", t], cwd=tmp_path, check=True)
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        assert soup.previous_tag("so", "so-v1.10.0") == "so-v1.2.0"
        assert soup.previous_tag("so", "so-v1.0.0") is None
        assert soup.previous_tag("so", "so-v2.0.0") == "so-v1.10.0"
    finally:
        os.chdir(cwd)


def test_manual_reports(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Prova_sicurezza_1.2.0_2026-11-01.md").write_text(
        "## 1. Identificazione\n\n| | |\n|---|---|\n| Prodotto e versione provata | so, 1.2.0, so-v1.2.0, sha256:x |\n\n"
        "## 2. Casi di prova\n\n| # | Requisito (codice) | Precondizioni | Passi | Risultato atteso | Risultato ottenuto | Esito |\n"
        "|---|---|---|---|---|---|---|\n| 1 | REQ-030 | | | | | superato |\n| 2 | REQ-031 | | | | | fallito |\n"
    )
    (docs / "Prova_vecchia_1.1.0_2026-10-01.md").write_text(
        "| | |\n|---|---|\n| Prodotto e versione provata | so-v1.1.0 |\n\n| # | Requisito (codice) | Esito |\n|---|---|---|\n| 1 | REQ-030 | superato |\n"
    )
    monkeypatch.chdir(tmp_path)
    cases = trace.manual_reports("1.2.0", "so-v1.2.0", "abcdef0123")
    assert cases == [
        {"requisito": "REQ-030", "test": "Prova_sicurezza_1.2.0_2026-11-01.md#1", "esito": "PASS"},
        {"requisito": "REQ-031", "test": "Prova_sicurezza_1.2.0_2026-11-01.md#2", "esito": "FAIL"},
    ]


def test_ensure_front_matter():
    md = draft.ensure_front_matter("```markdown\n# Titolo\n```", "1.2.0")
    assert md.startswith("---\nstato: bozza\n") and "# Titolo" in md
    md2 = draft.ensure_front_matter("---\ncodice: X\n---\n# T", "1.2.0")
    assert md2.startswith("---\nstato: bozza\ncodice: X")


def test_read_bundle_tronca(tmp_path):
    (tmp_path / "big.csv").write_text("x" * (draft.MAX_CHARS + 10))
    (tmp_path / "ignorato.json").write_text("{}")
    files = draft.read_bundle(tmp_path)
    assert set(files) == {"big.csv"} and "troncato" in files["big.csv"]
