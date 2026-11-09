"""Esecuzione completa di traceability, soup-evidence e test-evidence con Linear e GitHub finti.

È la validazione dello script della matrice richiesta da HE-SOP-003 par. 5 (HE-REC-002): dati minimi
nei formati della procedura, esito atteso riga per riga.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "actions" / "_lib"))
import helib as H  # noqa: E402


def load(name: str):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "actions" / name / "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


COMPONENTS = [{"name": "backend", "path": "app/backend", "kind": "python", "arc": "ARC-002"}]
PRODUCT = {"codice": "SO", "tag": "so", "copertura_minima": 80, "linear_progetto": "Prodotto"}

REQUISITI = """| Codice | Testo | User Need | ARC- | RC- | Stato |
|---|---|---|---|---|---|
| REQ-001 | Il backend risponde | 1 | ARC-002 | | approvato in R1 del 2026-10-01 |
| REQ-002 | La classe non è modificabile | 1 | ARC-002 | RC-07 | approvato in R1 del 2026-10-01 |
| REQ-003 | Vecchio | 1 | ARC-002 | | superato |
"""
USER_NEEDS = (
    "| Numero | Testo | Data | Recap | Stato |\n|---|---|---|---|---|\n| 1 | Vedere | 2026-09-01 | Recap | attivo |\n"
)
ARC_DOC = "## 2. Componenti\n\n| ARC- | Nome |\n|---|---|\n| ARC-002 | backend |\n"

ISSUES = [
    {
        "identifier": "H-10",
        "title": "Funzione",
        "description": "## Criteri\n\n---\nUser Need: 1 · Requisiti: REQ-001, REQ-002 · Verifica: RC-07",
        "state": {"type": "completed"},
        "labels": {"nodes": [{"name": "Funzionalità"}]},
        "parent": None,
        "children": {"nodes": [{"identifier": "H-11"}]},
    },
    {
        "identifier": "H-11",
        "title": "[BE] Api",
        "description": "",
        "state": {"type": "completed"},
        "labels": {"nodes": [{"name": "BE"}]},
        "parent": {"identifier": "H-10"},
        "children": {"nodes": []},
    },
]
PRS = [
    {
        "number": 5,
        "merged_at": "2026-10-10T10:00:00Z",
        "body": "Closes H-11\n- [x] ok",
        "title": "api",
        "user": {"login": "anna"},
        "head": {"ref": "feat/h-11-api"},
        "html_url": "https://x/5",
    }
]

JUNIT_BACKEND = """<testsuites><testsuite name="pytest">
<testcase classname="tests.unit.test_a" name="test_a" time="0.1"/>
<testcase classname="tests.integration.test_b" name="test_arc_002_api_risponde" time="0.2"/>
</testsuite></testsuites>"""
JUNIT_E2E = """<testsuites><testsuite name="pytest">
<testcase classname="tests.system.test_c" name="test_req_001_backend_risponde" time="0.3"/>
<testcase classname="tests.system.test_c" name="test_req_002_classe_non_modificabile" time="0.3"/>
</testsuite></testsuites>"""


@pytest.fixture
def repo(tmp_path, monkeypatch):
    (tmp_path / "docs" / "architecture").mkdir(parents=True)
    (tmp_path / "docs" / "architecture" / "SO-ARC-001.md").write_text(ARC_DOC)
    ev = tmp_path / "evidence"
    (ev / "test-backend").mkdir(parents=True)
    (ev / "test-backend" / "junit.xml").write_text(JUNIT_BACKEND)
    (ev / "test-backend" / "coverage.xml").write_text('<coverage line-rate="0.9"/>')
    (ev / "e2e").mkdir()
    (ev / "e2e" / "junit.xml").write_text(JUNIT_E2E)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("COMPONENTS", json.dumps(COMPONENTS))
    monkeypatch.setenv("PRODUCT", json.dumps(PRODUCT))
    monkeypatch.setenv("EVIDENCE", "evidence")
    monkeypatch.setenv("OUT", "out")
    monkeypatch.setenv("TAG", "so-v1.0.0")
    monkeypatch.setenv("GITHUB_REPOSITORY", "H-EALTH/x")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    return tmp_path


def fake_linear(monkeypatch, mod, requisiti=REQUISITI, issues=ISSUES):
    monkeypatch.setattr(mod.H, "linear_project", lambda ref: {"id": "p1", "name": "Prodotto"})
    monkeypatch.setattr(mod.H, "linear_documents", lambda pid: {"User Need": USER_NEEDS, "Requisiti": requisiti})
    monkeypatch.setattr(mod.H, "linear_issues", lambda pid: issues)


def test_traceability_ok(repo, monkeypatch):
    trace = load("traceability")
    fake_linear(monkeypatch, trace)
    monkeypatch.setattr(trace.H, "gh_api", lambda path, paginate=True, jq=None: PRS)
    trace.main()
    header, rows = H.read_csv(repo / "out" / "SO-REC-002_Matrice-tracciabilita.csv")
    assert header == trace.COLUMNS
    by = {(r["requisito"], r["test"]): r for r in rows}
    r1 = by[("REQ-001", "test_req_001_backend_risponde")]
    assert r1["issue"] == "H-10" and r1["pull_request"] == "#5" and r1["esito_test"] == "PASS"
    assert r1["componente_codice"] == "sistema" and r1["versione_rilascio"] == "so-v1.0.0" and r1["user_need"] == "1"
    r2 = by[("REQ-002", "test_req_002_classe_non_modificabile")]
    assert r2["rc"] == "RC-007" and r2["verifica_misura_rischio"] == "test_req_002_classe_non_modificabile"
    arc_row = by[("", "test_arc_002_api_risponde")]
    assert (
        arc_row["arc"] == "ARC-002"
        and arc_row["componente_codice"] == "backend"
        and arc_row["note"] == "test di integrazione"
    )
    assert not any(r["requisito"] == "REQ-003" for r in rows)  # superato
    assert (repo / "out" / "Requisiti_SO_").parent.exists() and list((repo / "out").glob("Requisiti_SO_*.md"))
    assert list((repo / "out").glob("UserNeed_SO_*.md"))


def test_traceability_chk(repo, monkeypatch, capsys):
    trace = load("traceability")
    requisiti = REQUISITI + "| REQ-004 | Senza test | 1 | ARC-002 | RC-09 | approvato |\n"
    issues = ISSUES + [
        {
            "identifier": "H-12",
            "title": "x",
            "description": "---\nRequisiti: REQ-099",
            "state": {"type": "completed"},
            "labels": {"nodes": []},
            "parent": None,
            "children": {"nodes": [{"identifier": "H-13"}]},
        },
        {
            "identifier": "H-13",
            "title": "[BE] senza pr",
            "description": "",
            "state": {"type": "completed"},
            "labels": {"nodes": []},
            "parent": {"identifier": "H-12"},
            "children": {"nodes": []},
        },
    ]
    fake_linear(monkeypatch, trace, requisiti, issues)
    monkeypatch.setattr(trace.H, "gh_api", lambda path, paginate=True, jq=None: PRS)
    (repo / "evidence" / "e2e" / "junit.xml").write_text(
        JUNIT_E2E.replace(
            '<testcase classname="tests.system.test_c" name="test_req_002_classe_non_modificabile" time="0.3"/>',
            '<testcase classname="tests.system.test_c" name="test_senza_codice" time="0.3"/>',
        )
    )
    with pytest.raises(SystemExit):
        trace.main()
    out = capsys.readouterr().out
    assert "CHK-001: H-12 cita REQ-099" in out
    assert "CHK-002: REQ-004 senza test" in out and "CHK-002: REQ-002 senza test" in out
    assert "CHK-003: test di sistema test_senza_codice" in out
    assert "CHK-004: REQ-004 attua RC-009" in out and "CHK-004: REQ-002 attua RC-007" in out
    assert "CHK-006: sotto-issue H-13 chiusa senza pull request" in out


def test_test_evidence(repo):
    te = load("test-evidence")
    te.main()
    header, rows = H.read_csv(repo / "out" / "test-report.csv")
    assert header == te.HEADER and len(rows) == 4
    assert {(r["test"], r["livello"], r["componente"]) for r in rows} == {
        ("test_a", "unit", "backend"),
        ("test_arc_002_api_risponde", "integration", "backend"),
        ("test_req_001_backend_risponde", "system", "sistema"),
        ("test_req_002_classe_non_modificabile", "system", "sistema"),
    }
    _, cov = H.read_csv(repo / "out" / "coverage.csv")
    assert cov == [{"componente": "backend", "copertura_percento": "90.00", "soglia_percento": "80", "esito": "ok"}]


def test_test_evidence_manca_e2e(repo, capsys):
    te = load("test-evidence")
    (repo / "evidence" / "e2e" / "junit.xml").unlink()
    with pytest.raises(SystemExit):
        te.main()
    assert "e2e/junit.xml" in capsys.readouterr().out


SCAN = {
    "Results": [
        {
            "Target": "requirements.txt",
            "Vulnerabilities": [
                {
                    "Severity": "HIGH",
                    "VulnerabilityID": "CVE-1",
                    "PkgName": "fastapi",
                    "InstalledVersion": "0.1",
                    "FixedVersion": "0.2",
                    "Status": "fixed",
                    "Title": "t",
                    "PrimaryURL": "u",
                }
            ],
        }
    ]
}
SBOM = {
    "packages": [
        {
            "name": "fastapi",
            "versionInfo": "0.115.0",
            "supplier": "Organization: Sebastián Ramírez",
            "externalRefs": [{"referenceType": "purl", "referenceLocator": "pkg:pypi/fastapi@0.115.0"}],
        }
    ]
}
SOUP_HEADER = "id,componente,produttore,versione,licenza,funzione_nel_prodotto,note\n"


@pytest.fixture
def soup_repo(repo, monkeypatch):
    (repo / "app" / "backend").mkdir(parents=True)
    (repo / "app" / "backend" / "Dockerfile").write_text("FROM python:3.12-slim@sha256:abc\n")
    (repo / "app" / "backend" / "requirements.txt").write_text("fastapi\n")
    (repo / "evidence" / "scan-backend").mkdir()
    (repo / "evidence" / "scan-backend" / "scan-backend.json").write_text(json.dumps(SCAN))
    (repo / "evidence" / "scan-backend-image").mkdir()
    (repo / "evidence" / "scan-backend-image" / "scan-backend-image.json").write_text(json.dumps({"Results": []}))
    (repo / "promote").mkdir()
    (repo / "promote" / "sbom-backend.spdx.json").write_text(json.dumps(SBOM))
    (repo / "docs" / "SO-REC-001_Lista-SOUP.csv").write_text(
        SOUP_HEADER + "SOUP-001,python (immagine python:3.12-slim),DA COMPILARE,3.12-slim,PSF,runtime,\n"
        "SOUP-002,fastapi,,0.100.0,MIT,api,\nSOUP-003,modello,DA DEFINIRE,DA DEFINIRE,,segnaposto,\n"
    )
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "a"], cwd=repo, check=True
    )
    subprocess.run(["git", "tag", "so-v0.9.0"], cwd=repo, check=True)
    monkeypatch.setenv("SBOM", "promote")
    return repo


def test_soup_evidence_ok(soup_repo):
    soup = load("soup-evidence")
    soup.main()
    _, scan = H.read_csv(soup_repo / "out" / "scan-report.csv")
    assert scan[0]["id"] == "CVE-1" and scan[0]["report"] == "fs" and scan[0]["componente"] == "backend"
    header, rec = H.read_csv(soup_repo / "out" / "SO-REC-001_Lista-SOUP.csv")
    byname = {r["componente"]: r for r in rec}
    assert byname["fastapi"]["versione"] == "0.115.0" and byname["fastapi"]["produttore"] == "Sebastián Ramírez"
    assert byname["python (immagine python:3.12-slim)"]["versione"] == "3.12-slim@sha256:abc"
    assert byname["modello"]["versione"] == "DA DEFINIRE"
    _, diff = H.read_csv(soup_repo / "out" / "soup-diff.csv")
    assert {(d["componente"], d["variazione"]) for d in diff} == {("fastapi", "aggiornato"), ("python", "aggiornato")}
    assert {d["da_versione"] for d in diff if d["componente"] == "fastapi"} == {"0.100.0"}


def test_soup_evidence_chk021(soup_repo, capsys):
    soup = load("soup-evidence")
    (soup_repo / "app" / "backend" / "requirements.txt").write_text("fastapi\nnumpy==2.0.0\n")
    with pytest.raises(SystemExit):
        soup.main()
    out = capsys.readouterr().out
    assert "CHK-021" in out and "numpy" in out
    _, rec = H.read_csv(soup_repo / "out" / "SO-REC-001_Lista-SOUP.csv")
    assert any(r["componente"] == "numpy" and r["note"].startswith("AGGIUNTA DALLA PIPELINE") for r in rec)
