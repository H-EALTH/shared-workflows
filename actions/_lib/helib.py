"""helib: funzioni comuni alle action di shared-workflows.

Legge solo codici e collegamenti nei formati di HE-SOP-003 (REQ-nnn, ARC-nnn, RC-nnn,
RSK-nnn, `Closes H-n` / `Part of H-n`, `test_req_nnn_...`, `test_arc_nnn_...`): nessuna
interpretazione, generazione deterministica (HE-SOP-003 par. 5). Solo libreria standard.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- codici -----------------------------------------------------------------------------

RE_REQ = re.compile(r"\bREQ-(\d{3})\b")
RE_ARC = re.compile(r"\bARC-(\d{3})\b")
RE_RC = re.compile(r"\bRC-(\d{2,3})\b")
RE_RSK = re.compile(r"\bRSK-(\d{2,3})\b")
RE_ISSUE = re.compile(r"\bH-(\d+)\b")
RE_TEST_CODE = re.compile(r"\btest_(req|arc)_(\d{3})(?=[_\W]|$)")

# HE-SOP-004 par. 2.1: branch `<tipo>/h-<numero>-<descrizione>`, in minuscolo
BRANCH_TYPES = ("feat", "fix", "hotfix", "docs", "refactor", "chore", "experiment", "test")
RE_BRANCH = re.compile(r"^(" + "|".join(BRANCH_TYPES) + r")/h-\d+-[a-z0-9][a-z0-9-]*$")

# .github/CONTRIBUTING.md dell'organizzazione: Closes (Fixes, Resolves, Completes) e
# Part of (Ref, Related to, Contributes to, Towards), nella descrizione della PR.
CLOSES_WORDS = ("Closes", "Fixes", "Resolves", "Completes")
PARTOF_WORDS = ("Part of", "Ref", "Related to", "Contributes to", "Towards")
RE_LINK = re.compile(
    r"\b(" + "|".join(CLOSES_WORDS + PARTOF_WORDS) + r")\s*:?\s+((?:H-\d+)(?:\s*,\s*H-\d+)*)",
    re.IGNORECASE,
)

RE_CHECKBOX = re.compile(r"^\s*[-*]\s+\[( |x|X)\]\s*(.*)$")
RE_NA = re.compile(r"\bN/A\s*:\s*\S")


def req(n: str | int) -> str:
    return f"REQ-{int(n):03d}"


def arc(n: str | int) -> str:
    return f"ARC-{int(n):03d}"


def norm_rc(code: str) -> str:
    """RC-07 e RC-007 sono lo stesso codice: forma canonica a tre cifre."""
    m = re.fullmatch(r"(RC|RSK)-(\d+)", code.strip().upper())
    return f"{m.group(1)}-{int(m.group(2)):03d}" if m else code.strip().upper()


# --- markdown -----------------------------------------------------------------------------


def md_tables(md: str) -> list[list[dict[str, str]]]:
    """Ogni tabella markdown come lista di righe {intestazione_minuscola: cella}.

    Le intestazioni sono normalizzate (minuscolo, spazi singoli, senza backtick); le celle
    conservano il testo originale senza spazi ai bordi. Le righe di separazione (---) sono
    scartate. Una tabella senza intestazione riconoscibile usa col0, col1, ...
    """
    tables, current, header = [], [], None
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s[1:-1].split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells):
                continue  # riga di separazione
            if header is None:
                header = [
                    re.sub(r"\s+", " ", c.replace("`", "").strip().lower()) or f"col{i}" for i, c in enumerate(cells)
                ]
                continue
            row = {header[i] if i < len(header) else f"col{i}": c for i, c in enumerate(cells)}
            current.append(row)
        else:
            if header is not None:
                tables.append(current)
            current, header = [], None
    if header is not None:
        tables.append(current)
    return tables


def _has(row: dict[str, str], *keys: str) -> bool:
    return any(re.search(r"(^|\W)" + re.escape(k) + r"(\W|$)", h) for h in row for k in keys)


def _col(row: dict[str, str], *keys: str) -> str:
    """Cella la cui intestazione contiene una delle parole chiave (come parola intera)."""
    for k in keys:
        for h, v in row.items():
            if re.search(r"(^|\W)" + re.escape(k) + r"(\W|$)", h):
                return v
    return ""


def _cell(row: dict[str, str], pos: int, *keys: str) -> str:
    """Per intestazione se la tabella ne ha una riconoscibile, altrimenti per posizione."""
    if _has(row, *keys):
        return _col(row, *keys)
    cells = list(row.values())
    return cells[pos] if len(cells) > pos else ""


def parse_requisiti(md: str) -> dict[str, dict[str, str]]:
    """Documento Requisiti (HE-SOP-003 par. 1): tabella con codice REQ-nnn, testo,
    User Need, ARC-, RC-, stato. Le colonne si riconoscono dall'intestazione; se manca,
    per posizione (codice, testo, user need, arc, rc, stato)."""
    out: dict[str, dict[str, str]] = {}
    for table in md_tables(md):
        for row in table:
            code_cell = _cell(row, 0, "codice", "requisito", "req")
            m = RE_REQ.search(code_cell)
            if not m:
                continue
            code = req(m.group(1))
            testo = _cell(row, 1, "testo", "descrizione")
            un = _cell(row, 2, "user need", "esigenza", "un")
            arc_cell = _cell(row, 3, "arc", "arc-", "componente")
            rc_cell = _cell(row, 4, "rc", "rc-", "misura", "rischio")
            stato = _cell(row, 5, "stato")
            un_num = re.search(r"\d+", un)
            out[code] = {
                "codice": code,
                "testo": testo,
                "user_need": un_num.group(0) if un_num else "",
                "arc": ", ".join(arc(x) for x in RE_ARC.findall(arc_cell)),
                "rc": ", ".join(norm_rc(f"RC-{x}") for x in RE_RC.findall(rc_cell)),
                "stato": stato.strip().lower(),
            }
    return out


def parse_user_needs(md: str) -> dict[str, dict[str, str]]:
    """Documento User Need: tabella numero, testo, data del colloquio, recap, stato."""
    out: dict[str, dict[str, str]] = {}
    for table in md_tables(md):
        for row in table:
            num_cell = _cell(row, 0, "numero", "user need", "n", "#")
            m = re.search(r"\d+", num_cell)
            if not m:
                continue
            out[m.group(0)] = {
                "numero": m.group(0),
                "testo": _cell(row, 1, "testo", "esigenza"),
                "stato": _cell(row, 4, "stato").strip().lower(),
            }
    return out


def parse_arc_codes(md: str) -> set[str]:
    """Codici ARC-nnn dei componenti dichiarati in <PROD>-ARC-001 (HE-TPL-018 par. 2): la
    prima cella delle righe della tabella la cui intestazione inizia con ARC. Se nessuna
    tabella ha quell'intestazione, tutti i codici ARC- del documento."""
    codes: set[str] = set()
    for table in md_tables(md):
        for row in table:
            keys = list(row.keys())
            if keys and keys[0].startswith("arc"):
                first = list(row.values())[0]
                codes.update(arc(x) for x in RE_ARC.findall(first))
    if not codes:
        codes.update(arc(x) for x in RE_ARC.findall(md))
    return codes


def parse_issue_footer(description: str) -> dict[str, object]:
    """Piè della issue o della PR (HE-SOP-003 par. 4 punto 4): `User Need: 4 · Requisiti: REQ-012, REQ-013`
    oppure `Verifica: REQ-012, RC-07`. Se il piè manca, i codici REQ- della sezione
    «Criteri di accettazione»."""
    text = description or ""
    user_need, requisiti, verifica_req, rc = "", [], [], []
    footer_found = False
    for line in text.splitlines():
        s = line.strip()
        if re.search(r"\b(Requisiti|Verifica)\s*:", s) and (RE_REQ.search(s) or RE_RC.search(s)):
            footer_found = True
            m = re.search(r"User Need\s*:\s*(\d+)", s, re.IGNORECASE)
            if m:
                user_need = m.group(1)
            for part in re.split(r"[·•]|\s{2,}", s):
                if re.search(r"\bRequisiti\s*:", part):
                    requisiti += [req(x) for x in RE_REQ.findall(part)]
                elif re.search(r"\bVerifica\s*:", part):
                    verifica_req += [req(x) for x in RE_REQ.findall(part)]
                    rc += [norm_rc(f"RC-{x}") for x in RE_RC.findall(part)]
    if not footer_found:
        sec = re.split(r"(?im)^#+\s*criteri di accettazione\s*$", text)
        if len(sec) > 1:
            body = re.split(r"(?m)^#+\s", sec[1])[0]
            requisiti = [req(x) for x in RE_REQ.findall(body)]
            rc = [norm_rc(f"RC-{x}") for x in RE_RC.findall(body)]
    return {
        "user_need": user_need,
        "requisiti": sorted(set(requisiti)),
        "verifica": sorted(set(verifica_req)),
        "rc": sorted(set(rc)),
        "rsk": sorted({norm_rc(f"RSK-{x}") for x in RE_RSK.findall(text)}),
    }


# --- pull request ---------------------------------------------------------------------------


def pr_links(body: str) -> list[tuple[str, str]]:
    """[(\"closes\"|\"partof\", \"H-91\"), ...] dalla descrizione della PR."""
    out = []
    for m in RE_LINK.finditer(body or ""):
        rel = "closes" if m.group(1).lower() in {w.lower() for w in CLOSES_WORDS} else "partof"
        for issue in re.findall(r"H-\d+", m.group(2), re.IGNORECASE):
            out.append((rel, issue.upper()))
    return out


def check_dod(body: str) -> list[str]:
    """Definizione di fatto (HE-SOP-003 par. 4.1): ogni casella `[x]`, oppure `[ ]` con
    `N/A: motivo`. Nessuna casella = modello di PR non usato."""
    problems, boxes = [], 0
    for line in (body or "").splitlines():
        m = RE_CHECKBOX.match(line)
        if not m:
            continue
        boxes += 1
        checked, text = m.group(1).lower() == "x", m.group(2)
        if not checked and not RE_NA.search(text):
            problems.append(f"casella non spuntata e senza `N/A: motivo`: {text.strip()[:80]}")
    if boxes == 0:
        problems.append("nessuna casella della definizione di fatto: usare .github/PULL_REQUEST_TEMPLATE.md")
    return problems


def check_dockerfile(text: str) -> list[str]:
    """Ogni FROM pinnato al digest `@sha256:` (CHK-019). Sono esclusi `FROM scratch`
    e i riferimenti a stage precedenti (`FROM builder`)."""
    stages, problems = set(), []
    for n, line in enumerate(text.splitlines(), 1):
        s = line.split("#", 1)[0].strip()
        if not s.upper().startswith("FROM "):
            continue
        parts = [p for p in s.split()[1:] if not p.startswith("--")]
        if not parts:
            continue
        ref = parts[0]
        if len(parts) >= 3 and parts[1].upper() == "AS":
            stages.add(parts[2])
        if ref in stages or ref == "scratch" or ref.startswith("$"):
            continue
        if "@sha256:" not in ref:
            problems.append(f"riga {n}: `{s}` senza digest @sha256:")
    return problems


def test_codes(text: str) -> list[tuple[str, str]]:
    """[(\"req\", \"REQ-012\"), (\"arc\", \"ARC-003\")] dai nomi di test in un file."""
    out = []
    for kind, num in RE_TEST_CODE.findall(text):
        out.append((kind, req(num) if kind == "req" else arc(num)))
    return out


def is_test_file(path: str) -> bool:
    p = path.replace("\\", "/")
    return "/tests/" in f"/{p}" or re.search(r"(^|/)test_[^/]*\.py$|\.(test|spec)\.[cm]?[jt]sx?$", p) is not None


# --- junit ----------------------------------------------------------------------------------


def parse_junit(path: str | Path) -> list[dict[str, str]]:
    """Casi di test di un junit.xml (pytest, vitest): suite, classname, name, file, result, time_s."""
    rows = []
    root = ET.parse(str(path)).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    for ts in suites:
        for tc in ts.findall("testcase"):
            res = (
                "FAIL"
                if tc.find("failure") is not None
                else "ERROR"
                if tc.find("error") is not None
                else "SKIP"
                if tc.find("skipped") is not None
                else "PASS"
            )
            rows.append(
                {
                    "suite": ts.get("name", ""),
                    "classname": tc.get("classname", ""),
                    "name": tc.get("name", ""),
                    "file": tc.get("file", ""),
                    "result": res,
                    "time_s": tc.get("time", ""),
                }
            )
    return rows


def test_level(row: dict[str, str], default: str = "") -> str:
    """unit / integration / system dal percorso del test (classname pytest `tests.unit.x`, file
    vitest `tests/unit/x.test.ts`); altrimenti il livello passato."""
    hay = " ".join([row.get("classname", ""), row.get("file", ""), row.get("suite", "")]).lower()
    for level in ("unit", "integration", "system"):
        if re.search(r"(^|[./\\ ])" + level + r"([./\\ ]|$)", hay):
            return level
    return default


def test_code_of(name: str) -> tuple[str, str] | None:
    m = RE_TEST_CODE.search(name)
    if not m:
        return None
    return (m.group(1), req(m.group(2)) if m.group(1) == "req" else arc(m.group(2)))


def coverage_rate(path: str | Path) -> str:
    """Copertura in percento (due decimali) da un coverage.xml cobertura (pytest-cov, vitest)."""
    root = ET.parse(str(path)).getroot()
    rate = root.get("line-rate")
    if rate is None:
        return ""
    return f"{float(rate) * 100:.2f}"


# --- csv e file -------------------------------------------------------------------------------


def write_csv(path: str | Path, header: list[str], rows: list[list | dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(h, "") for h in header] if isinstance(r, dict) else r)


def read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        return list(rd.fieldnames or []), list(rd)


def fail(msg: str) -> None:
    print(f"::error::{msg}")
    sys.exit(1)


def warn(msg: str) -> None:
    print(f"::warning::{msg}")


def summary(text: str) -> None:
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


def set_output(name: str, value: str) -> None:
    p = os.environ.get("GITHUB_OUTPUT")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            if "\n" in value:
                f.write(f"{name}<<EOF\n{value}\nEOF\n")
            else:
                f.write(f"{name}={value}\n")


# --- GitHub (gh CLI) -------------------------------------------------------------------------


def gh_api(path: str, paginate: bool = True, jq: str | None = None) -> list | dict | str:
    cmd = ["gh", "api", path]
    if paginate:
        cmd += ["--paginate", "--slurp"]
    if jq:
        cmd += ["--jq", jq]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    if jq:
        return out
    data = json.loads(out or "null")
    if paginate and isinstance(data, list) and data and isinstance(data[0], list):
        return [x for page in data for x in page]
    return data


def frozen_export(title: str, product: str, content: str, source: str) -> str:
    """Export congelato di un documento (HE-SOP-003 par. 5), con intestazione."""
    from datetime import date

    return (
        f"---\ntitolo: {title}\nprodotto: {product}\ndata: {date.today().isoformat()}\n"
        f"origine: {source}\nstato: congelato\n---\n\n{content.rstrip()}\n"
    )


def component_of(path: str, components: list[dict]) -> str:
    """Nome del componente (cartella) a cui appartiene un file; vuoto se nessuno."""
    p = re.sub(r"^\./", "", path.replace("\\", "/"))
    best = ""
    for c in components:
        cp = c["path"].rstrip("/") + "/"
        if p.startswith(cp) and len(cp) > len(best):
            best = c["name"]
    return best
