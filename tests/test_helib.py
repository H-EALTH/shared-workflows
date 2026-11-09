"""Test della libreria comune: i formati di HE-SOP-003 letti dalle action."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "actions" / "_lib"))
import helib as H  # noqa: E402

REQUISITI = """# Requisiti

| Codice | Testo | User Need | ARC- | RC- | Stato |
|---|---|---|---|---|---|
| REQ-001 | Il sistema mostra la settimana | 4 | ARC-001 | | approvato in R1 del 2026-10-01 |
| REQ-002 | La classe di priorità non è modificabile | 2 | ARC-002, ARC-003 | RC-07 | approvato in R1 del 2026-10-01 |
| REQ-003 | Vecchio requisito | 1 | ARC-001 | | superato |
"""

REQUISITI_SENZA_INTESTAZIONE = """| | | | | | |
|---|---|---|---|---|---|
| REQ-010 | testo | 3 | ARC-002 | RC-001 | proposto |
"""

ARC = """## 2. Componenti

| ARC- | Nome | Cosa fa | Classe |
|---|---|---|---|
| ARC-001 | frontend | interfaccia | A |
| ARC-002 | backend API | api | B |

## 3. Interfacce

| Da | A | Tipo |
|---|---|---|
| ARC-001 | ARC-002 | interna |
| ARC-002 | ARC-009 | esterna |
"""


def test_parse_requisiti_per_intestazione():
    r = H.parse_requisiti(REQUISITI)
    assert set(r) == {"REQ-001", "REQ-002", "REQ-003"}
    assert r["REQ-002"] == {
        "codice": "REQ-002",
        "testo": "La classe di priorità non è modificabile",
        "user_need": "2",
        "arc": "ARC-002, ARC-003",
        "rc": "RC-007",
        "stato": "approvato in r1 del 2026-10-01",
    }
    assert r["REQ-003"]["stato"] == "superato"
    assert r["REQ-001"]["rc"] == ""


def test_parse_requisiti_per_posizione():
    r = H.parse_requisiti(REQUISITI_SENZA_INTESTAZIONE)
    assert r["REQ-010"]["arc"] == "ARC-002" and r["REQ-010"]["rc"] == "RC-001" and r["REQ-010"]["user_need"] == "3"


def test_parse_user_needs():
    md = "| Numero | Testo | Data | Recap | Stato |\n|---|---|---|---|---|\n| 1 | Vedere la settimana | 2026-09-01 | Recap_x | attivo |\n| 2 | Altro | | | superato |"
    un = H.parse_user_needs(md)
    assert un["1"]["testo"] == "Vedere la settimana" and un["2"]["stato"] == "superato"


def test_parse_arc_codes_solo_tabella_componenti():
    assert H.parse_arc_codes(ARC) == {"ARC-001", "ARC-002"}


def test_parse_arc_codes_senza_tabella():
    assert H.parse_arc_codes("ARC-005 e ARC-007 nel testo") == {"ARC-005", "ARC-007"}


def test_issue_footer():
    desc = "## Contesto\nx\n## Criteri di accettazione\n1. REQ-099 ignorato perché c'è il piè\n\n---\nUser Need: 4 · Requisiti: REQ-012, REQ-013 · Verifica: REQ-014, RC-07"
    f = H.parse_issue_footer(desc)
    assert f == {
        "user_need": "4",
        "requisiti": ["REQ-012", "REQ-013"],
        "verifica": ["REQ-014"],
        "rc": ["RC-007"],
        "rsk": [],
    }


def test_issue_footer_da_criteri():
    desc = "## Criteri di accettazione\n- REQ-020 testo (controllo del rischio RC-003)\n- REQ-021 testo\n## Note tecniche\nREQ-999"
    f = H.parse_issue_footer(desc)
    assert f["requisiti"] == ["REQ-020", "REQ-021"] and f["rc"] == ["RC-003"] and f["user_need"] == ""


@pytest.mark.parametrize(
    "body,expected",
    [
        ("Closes H-91", [("closes", "H-91")]),
        ("Part of H-91, H-92", [("partof", "H-91"), ("partof", "H-92")]),
        ("fixes h-5", [("closes", "H-5")]),
        ("Related to H-7 e Towards H-8", [("partof", "H-7"), ("partof", "H-8")]),
        ("nessun collegamento H-3", []),
    ],
)
def test_pr_links(body, expected):
    assert H.pr_links(body) == expected


def test_dod_ok():
    body = "Closes H-1\n- [x] revisione\n- [X] test\n- [ ] N/A: nessuna documentazione toccata\n"
    assert H.check_dod(body) == []


def test_dod_ko():
    assert any("non spuntata" in p for p in H.check_dod("- [x] a\n- [ ] b\n"))
    assert any("nessuna casella" in p for p in H.check_dod("Closes H-1"))
    assert any("non spuntata" in p for p in H.check_dod("- [ ] N/A senza motivo"))


@pytest.mark.parametrize(
    "name,expected",
    [
        ("feat/h-91-validazione-cf", True),
        ("hotfix/h-1-x", True),
        ("feat/H-91-x", False),
        ("feature/h-91-x", False),
        ("feat/h-91", False),
        ("feat/h-91-Maiuscola", False),
    ],
)
def test_branch(name, expected):
    assert bool(H.RE_BRANCH.match(name)) is expected


def test_dockerfile():
    df = """FROM python:3.12-slim@sha256:aaaa AS build
FROM --platform=linux/amd64 node:24@sha256:bbbb AS web
FROM build
FROM scratch
FROM nginx:1.30  # non pinnato
FROM ${BASE}
"""
    problems = H.check_dockerfile(df)
    assert len(problems) == 1 and "nginx:1.30" in problems[0] and "riga 5" in problems[0]


def test_test_codes():
    src = (
        "def test_req_012_classe(): ...\ndef test_arc_003_risolutore(): ...\nit('test_req_013 fa x')\ntest_request_1()"
    )
    assert H.test_codes(src) == [("req", "REQ-012"), ("arc", "ARC-003"), ("req", "REQ-013")]
    assert H.test_code_of("test_req_012_classe_non_modificata") == ("req", "REQ-012")
    assert H.test_code_of("test_classe") is None


@pytest.mark.parametrize(
    "path,expected",
    [
        ("app/backend/tests/unit/test_x.py", True),
        ("app/frontend/src/x.test.ts", True),
        ("app/backend/main.py", False),
        ("tests/system/test_req_001.py", True),
    ],
)
def test_is_test_file(path, expected):
    assert H.is_test_file(path) is expected


JUNIT = """<?xml version="1.0"?>
<testsuites><testsuite name="pytest" tests="3" failures="1">
<testcase classname="tests.unit.test_a" name="test_a" time="0.1"/>
<testcase classname="tests.integration.test_b" name="test_arc_003_risponde" time="0.2"><failure/></testcase>
<testcase classname="tests.system.test_c" name="test_req_012_x" file="tests/system/test_c.py" time="0.3"><skipped/></testcase>
</testsuite></testsuites>"""


def test_junit(tmp_path):
    p = tmp_path / "junit.xml"
    p.write_text(JUNIT)
    rows = H.parse_junit(p)
    assert [r["result"] for r in rows] == ["PASS", "FAIL", "SKIP"]
    assert [H.test_level(r) for r in rows] == ["unit", "integration", "system"]
    assert H.test_level({"classname": "foo", "file": "", "suite": ""}, "system") == "system"


def test_coverage(tmp_path):
    p = tmp_path / "coverage.xml"
    p.write_text('<?xml version="1.0"?><coverage line-rate="0.8765" branch-rate="0"></coverage>')
    assert H.coverage_rate(p) == "87.65"


def test_md_tables_senza_intestazione():
    t = H.md_tables("| | |\n|---|---|\n| Prodotto e versione provata | so-ulss2-v1.2.0 |\n")
    assert t == [[{"col0": "Prodotto e versione provata", "col1": "so-ulss2-v1.2.0"}]]


def test_component_of():
    comps = [{"name": "backend", "path": "app/backend"}, {"name": "api", "path": "app/backend/api"}]
    assert H.component_of("app/backend/api/tests/test_x.py", comps) == "api"
    assert H.component_of("./app/backend/main.py", comps) == "backend"
    assert H.component_of("tests/system/test_x.py", comps) == ""


def test_norm_rc():
    assert H.norm_rc("RC-7") == "RC-007" and H.norm_rc("RSK-07") == "RSK-007"


def test_csv_roundtrip(tmp_path):
    p = tmp_path / "x.csv"
    H.write_csv(p, ["a", "b"], [{"a": "1", "b": "2"}, ["3", "4"]])
    header, rows = H.read_csv(p)
    assert header == ["a", "b"] and rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
