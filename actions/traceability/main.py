"""traceability: <PROD>-REC-002_Matrice-tracciabilita.csv + export congelati di User Need e Requisiti.

Variabili: COMPONENTS, PRODUCT (JSON), EVIDENCE, OUT (cartelle), TAG, LINEAR_API_KEY, GH_TOKEN,
GITHUB_REPOSITORY, GITHUB_SHA.

Colonne fisse (HE-SOP-003 par. 5): user_need, requisito, arc, issue, pull_request,
componente_codice, test, esito_test, rsk, rc, verifica_misura_rischio, versione_rilascio, note.
Una riga per coppia (requisito, test); una riga per requisito senza test; una riga per test di
integrazione (codice ARC-). `componente_codice` è la cartella del componente del repository che
contiene il test (`sistema` per tests/system).
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

COLUMNS = [
    "user_need",
    "requisito",
    "arc",
    "issue",
    "pull_request",
    "componente_codice",
    "test",
    "esito_test",
    "rsk",
    "rc",
    "verifica_misura_rischio",
    "versione_rilascio",
    "note",
]
ATTIVITA = "attività"


def labels_of(issue: dict) -> set[str]:
    return {label["name"].strip().lower() for label in (issue.get("labels") or {}).get("nodes", [])}


def is_done(issue: dict) -> bool:
    return (issue.get("state") or {}).get("type") == "completed"


def is_canceled(issue: dict) -> bool:
    return (issue.get("state") or {}).get("type") == "canceled"


def manual_reports(version: str, tag: str, sha: str) -> list[dict]:
    """Casi di prova dei rapporti HE-TPL-024 in docs/ riferiti a questa versione (tag, x.y.z,
    oppure SHA del commit)."""
    cases = []
    for path in sorted(Path("docs").rglob("Prova_*.md")):
        md = path.read_text(encoding="utf-8", errors="replace")
        tables = H.md_tables(md)
        ident_text = " ".join(
            " ".join(r.values()) for t in tables for r in t if r and "versione provata" in list(r.values())[0].lower()
        )
        if not any(x and x in ident_text for x in (tag, version, sha[:7], sha)):
            H.warn(f"{path}: non cita la versione {tag} ({version}, {sha[:7]}): non entra nella matrice")
            continue
        for table in tables:
            for row in table:
                code_cell = H._col(row, "requisito")
                esito = H._col(row, "esito").strip().lower()
                num = H._col(row, "#")
                for n in H.RE_REQ.findall(code_cell):
                    cases.append(
                        {
                            "requisito": H.req(n),
                            "test": f"{path.name}#{num or '?'}",
                            "esito": "PASS"
                            if esito.startswith("superat")
                            else "FAIL"
                            if esito.startswith("fall")
                            else "SKIP",
                        }
                    )
    return cases


def main() -> None:
    components = json.loads(os.environ["COMPONENTS"])
    product = json.loads(os.environ["PRODUCT"])
    evidence, out = Path(os.environ["EVIDENCE"]), Path(os.environ["OUT"])
    tag, repo, sha = os.environ["TAG"], os.environ["GITHUB_REPOSITORY"], os.environ.get("GITHUB_SHA", "")
    codice = product["codice"]
    version = tag.rsplit("-v", 1)[-1]
    out.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    # --- Linear: documenti e issue
    ref = product.get("linear_progetto")
    if not ref:
        H.fail("product.yaml: manca `linear_progetto` (nome, slug o id del progetto Linear)")
    project = H.linear_project(ref)
    docs = H.linear_documents(project["id"])
    un_md, req_md = H.linear_document(docs, "User Need"), H.linear_document(docs, "Requisiti")
    user_needs = H.parse_user_needs(un_md)
    requisiti = {k: v for k, v in H.parse_requisiti(req_md).items() if not v["stato"].startswith("superat")}
    if not requisiti:
        H.fail("documento Requisiti di Linear senza requisiti attivi (REQ-nnn)")
    today = date.today().isoformat()
    (out / f"UserNeed_{codice}_{today}.md").write_text(
        H.frozen_export("User Need", codice, un_md, f"Linear, progetto {project['name']}, tag {tag}"), encoding="utf-8"
    )
    (out / f"Requisiti_{codice}_{today}.md").write_text(
        H.frozen_export("Requisiti", codice, req_md, f"Linear, progetto {project['name']}, tag {tag}"), encoding="utf-8"
    )

    arc_doc = Path("docs/architecture") / f"{codice}-ARC-001.md"
    arc_codes = H.parse_arc_codes(arc_doc.read_text(encoding="utf-8")) if arc_doc.is_file() else set()

    issues = [i for i in H.linear_issues(project["id"]) if not is_canceled(i)]
    by_id = {i["identifier"]: i for i in issues}
    parents = {i["identifier"]: i for i in issues if not i.get("parent")}
    children = {i["identifier"]: i for i in issues if i.get("parent")}
    footers = {k: H.parse_issue_footer(v.get("description") or "") for k, v in parents.items()}

    # CHK-001 sui codici citati nelle issue
    for k, f in footers.items():
        for code in f["requisiti"] + f["verifica"]:
            if code not in requisiti and code not in H.parse_requisiti(req_md):
                errors.append(f"CHK-001: {k} cita {code}, che non esiste nel documento Requisiti")

    # --- GitHub: pull request fuse → sotto-issue → issue madre
    prs = [p for p in H.gh_api(f"repos/{repo}/pulls?state=closed&per_page=100") if p.get("merged_at")]
    prs_of_issue: dict[str, list[str]] = {}
    for p in prs:
        for _, iss in H.pr_links(p.get("body") or ""):
            prs_of_issue.setdefault(iss, []).append(f"#{p['number']}")
    prs_of_parent: dict[str, list[str]] = {}
    for k, c in children.items():
        parent = c["parent"]["identifier"]
        prs_of_parent.setdefault(parent, []).extend(prs_of_issue.get(k, []))
    for k in parents:  # una issue senza figlie può avere la PR direttamente
        prs_of_parent.setdefault(k, []).extend(prs_of_issue.get(k, []))

    # CHK-006: sotto-issue chiusa senza pull request, o senza madre nota
    for k, c in children.items():
        parent_id = c["parent"]["identifier"]
        parent = by_id.get(parent_id)
        if parent is None:
            errors.append(f"CHK-006: sotto-issue {k} con madre {parent_id} fuori dal progetto o cancellata")
            continue
        if ATTIVITA in labels_of(parent) or ATTIVITA in labels_of(c):
            continue
        if is_done(c) and not prs_of_issue.get(k):
            errors.append(f"CHK-006: sotto-issue {k} chiusa senza pull request con `Closes {k}` o `Part of {k}`")

    # --- test automatici di integrazione e sistema (JUnit del run ci)
    tests: list[dict] = []  # {kind, code, name, result, component, level}
    for c in components:
        junit = evidence / f"test-{c['name']}" / "junit.xml"
        if not junit.is_file():
            H.fail(f"manca {junit} nel run ci")
        for t in H.parse_junit(junit):
            level = H.test_level(t, "unit")
            if level == "unit":
                continue
            code = H.test_code_of(t["name"])
            if not code:
                errors.append(f"CHK-003: test {t['name']} ({c['name']}, {level}) senza codice REQ-/ARC- nel nome")
                continue
            tests.append(
                {
                    "kind": code[0],
                    "code": code[1],
                    "name": t["name"],
                    "result": t["result"],
                    "component": c["name"],
                    "level": level,
                }
            )
    e2e = evidence / "e2e" / "junit.xml"
    if not e2e.is_file():
        H.fail(f"manca {e2e} nel run ci")
    for t in H.parse_junit(e2e):
        code = H.test_code_of(t["name"])
        if not code:
            errors.append(f"CHK-003: test di sistema {t['name']} senza codice REQ- nel nome")
            continue
        tests.append(
            {
                "kind": code[0],
                "code": code[1],
                "name": t["name"],
                "result": t["result"],
                "component": "sistema",
                "level": "system",
            }
        )
    for t in tests:
        if t["kind"] == "req" and t["code"] not in requisiti:
            errors.append(f"CHK-001: test {t['name']} cita {t['code']}, non attivo nel documento Requisiti")
        if t["kind"] == "arc" and arc_codes and t["code"] not in arc_codes:
            errors.append(f"CHK-001: test {t['name']} cita {t['code']}, che non esiste in {arc_doc.name}")

    manual = manual_reports(version, tag, sha)
    for m in manual:
        if m["requisito"] not in requisiti:
            errors.append(f"CHK-001: {m['test']} cita {m['requisito']}, non attivo nel documento Requisiti")

    # --- matrice
    rows: list[dict] = []
    for code, r in sorted(requisiti.items()):
        issue_ids = sorted(k for k, f in footers.items() if code in f["requisiti"] or code in f["verifica"])
        pr_list = sorted({p for k in issue_ids for p in prs_of_parent.get(k, [])}, key=lambda s: int(s[1:]))
        rsk = sorted(
            {x for k in issue_ids for x in footers[k]["rsk"]}
            | {H.norm_rc(f"RSK-{n}") for k in issue_ids for n in H.RE_RSK.findall(parents[k]["title"])}
        )
        rc = sorted(set(filter(None, r["rc"].split(", "))) | {x for k in issue_ids for x in footers[k]["rc"]})
        evidence_tests = [t for t in tests if t["kind"] == "req" and t["code"] == code] + [
            {"name": m["test"], "result": m["esito"], "component": "manuale"} for m in manual if m["requisito"] == code
        ]
        passed = [t["name"] for t in evidence_tests if t["result"] == "PASS"]
        base = {
            "user_need": r["user_need"],
            "requisito": code,
            "arc": r["arc"],
            "issue": " ".join(issue_ids),
            "pull_request": " ".join(pr_list),
            "rsk": " ".join(rsk),
            "rc": " ".join(rc),
            "verifica_misura_rischio": " ".join(passed) if rc else "",
            "versione_rilascio": tag,
            "note": "",
        }
        if not evidence_tests:
            errors.append(f"CHK-002: {code} senza test automatico superato né rapporto di prova manuale")
            rows.append(base | {"componente_codice": "", "test": "", "esito_test": "", "note": "requisito senza test"})
        elif not passed:
            errors.append(f"CHK-002: {code} ha test ma nessuno superato")
        if rc and not passed:
            errors.append(f"CHK-004: {code} attua {' '.join(rc)} senza un test superato che ne verifichi l'efficacia")
        if r["user_need"] and r["user_need"] not in user_needs:
            errors.append(f"CHK-001: {code} cita User Need {r['user_need']}, assente nel documento User Need")
        for t in evidence_tests:
            rows.append(base | {"componente_codice": t["component"], "test": t["name"], "esito_test": t["result"]})
    for t in sorted(tests, key=lambda t: (t["code"], t["name"])):
        if t["kind"] == "arc":
            rows.append(
                {
                    "user_need": "",
                    "requisito": "",
                    "arc": t["code"],
                    "issue": "",
                    "pull_request": "",
                    "componente_codice": t["component"],
                    "test": t["name"],
                    "esito_test": t["result"],
                    "rsk": "",
                    "rc": "",
                    "verifica_misura_rischio": "",
                    "versione_rilascio": tag,
                    "note": "test di integrazione",
                }
            )
    H.write_csv(out / f"{codice}-REC-002_Matrice-tracciabilita.csv", COLUMNS, rows)

    n_req = len(requisiti)
    covered = sum(1 for c in requisiti if any(r["requisito"] == c and r["esito_test"] == "PASS" for r in rows))
    lines = [
        "### traceability",
        "",
        f"{n_req} requisiti attivi, {covered} con test superato · {len(tests)} test con codice · "
        f"{len(manual)} casi manuali · {len(prs)} pull request fuse",
        "",
    ]
    if errors:
        lines += ["| controllo | dettaglio |", "|---|---|"] + [
            f"| {e.split(':', 1)[0]} | {e.split(':', 1)[1].strip()} |" for e in errors
        ]
    H.summary("\n".join(lines))
    for e in errors:
        print(f"::error::{e}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
