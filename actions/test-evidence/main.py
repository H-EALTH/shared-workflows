"""test-evidence: test-report.csv e coverage.csv dagli artifact test-<comp> ed e2e del run ci.

Variabili: COMPONENTS (JSON), PRODUCT (JSON), EVIDENCE (cartella), OUT (cartella).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

HEADER = ["test", "componente", "livello", "esito", "durata_s", "codice", "classname"]


def main() -> None:
    components = json.loads(os.environ["COMPONENTS"])
    product = json.loads(os.environ["PRODUCT"])
    ev = Path(os.environ["EVIDENCE"])
    out = Path(os.environ["OUT"])
    soglia = float(product.get("copertura_minima", 0))

    rows, cov, missing = [], [], []
    for c in components:
        junit = ev / f"test-{c['name']}" / "junit.xml"
        if not junit.is_file():
            missing.append(str(junit))
            continue
        for t in H.parse_junit(junit):
            code = H.test_code_of(t["name"])
            rows.append(
                {
                    "test": t["name"],
                    "componente": c["name"],
                    "livello": H.test_level(t, "unit"),
                    "esito": t["result"],
                    "durata_s": t["time_s"],
                    "codice": code[1] if code else "",
                    "classname": t["classname"] or t["file"],
                }
            )
        coverage = ev / f"test-{c['name']}" / "coverage.xml"
        if coverage.is_file():
            pct = H.coverage_rate(coverage)
            cov.append([c["name"], pct, f"{soglia:g}", "ok" if pct and float(pct) >= soglia else "sotto soglia"])
        else:
            missing.append(str(coverage))

    e2e = ev / "e2e" / "junit.xml"
    if e2e.is_file():
        for t in H.parse_junit(e2e):
            code = H.test_code_of(t["name"])
            rows.append(
                {
                    "test": t["name"],
                    "componente": "sistema",
                    "livello": "system",
                    "esito": t["result"],
                    "durata_s": t["time_s"],
                    "codice": code[1] if code else "",
                    "classname": t["classname"] or t["file"],
                }
            )
    else:
        missing.append(str(e2e))

    if missing:
        H.fail("JUnit o coverage attesi e non trovati nel run ci: " + ", ".join(missing))

    H.write_csv(out / "test-report.csv", HEADER, rows)
    H.write_csv(out / "coverage.csv", ["componente", "copertura_percento", "soglia_percento", "esito"], cov)

    tot = {k: sum(1 for r in rows if r["esito"] == k) for k in ("PASS", "FAIL", "ERROR", "SKIP")}
    lines = [
        "### test-evidence",
        "",
        f"{len(rows)} test · " + " · ".join(f"{k} {v}" for k, v in tot.items()),
        "",
        "| componente | copertura | soglia | esito |",
        "|---|---|---|---|",
    ]
    lines += [f"| {r[0]} | {r[1]}% | {r[2]}% | {r[3]} |" for r in cov]
    H.summary("\n".join(lines))
    if tot["FAIL"] or tot["ERROR"]:
        H.fail(f"il run ci contiene test non superati: FAIL {tot['FAIL']}, ERROR {tot['ERROR']}")


if __name__ == "__main__":
    main()
