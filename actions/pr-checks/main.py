"""pr-checks: le regole QMS sulla pull request. Non costruisce, non blocca build: solo ci-ok.

Variabili: PRODUCT (JSON di product.yaml), PR (numero), GH_TOKEN, GITHUB_REPOSITORY, LINEAR_API_KEY.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

DEPENDABOT = {"dependabot[bot]"}


def main() -> None:
    product = json.loads(os.environ["PRODUCT"])
    repo = os.environ["GITHUB_REPOSITORY"]
    pr = os.environ["PR"]
    codice = product["codice"]

    meta = H.gh_api(f"repos/{repo}/pulls/{pr}", paginate=False)
    files = H.gh_api(f"repos/{repo}/pulls/{pr}/files")
    body = meta.get("body") or ""
    branch = meta["head"]["ref"]
    author = meta["user"]["login"]
    bot = author in DEPENDABOT or branch.startswith("dependabot/")
    changed = [f["filename"] for f in files if f.get("status") != "removed"]

    errors: list[tuple[str, str]] = []  # (controllo, messaggio)

    # 1. nome del branch (HE-SOP-004 par. 2.1)
    if bot:
        print(f"branch `{branch}` di Dependabot: nome non verificato (HE-SOP-004 par. 3.2)")
    elif not H.RE_BRANCH.match(branch):
        errors.append(
            (
                "branch",
                f"`{branch}` non è `<tipo>/h-<numero>-<descrizione>` in minuscolo (tipi: {', '.join(H.BRANCH_TYPES)})",
            )
        )

    # 2. collegamento alla sotto-issue (HE-SOP-003 par. 4 punto 8, CHK-005)
    links = H.pr_links(body)
    if not links:
        errors.append(
            (
                "closes",
                "la descrizione non contiene `Closes H-n` né `Part of H-n` "
                "(vedi .github/CONTRIBUTING.md dell'organizzazione)",
            )
        )

    # 3. definizione di fatto (HE-SOP-003 par. 4.1, CHK-008)
    for p in H.check_dod(body):
        errors.append(("definizione di fatto", p))

    # 4. codici dei test nei file toccati (HE-SOP-003 par. 4 punto 9, CHK-001)
    arc_doc = Path("docs/architecture") / f"{codice}-ARC-001.md"
    arc_codes = H.parse_arc_codes(arc_doc.read_text(encoding="utf-8")) if arc_doc.exists() else set()
    if not arc_doc.exists():
        errors.append(("arc", f"manca {arc_doc} (HE-SOP-004 par. 1.2)"))
    req_codes: set[str] | None = None
    for f in changed:
        if not H.is_test_file(f) or not Path(f).is_file():
            continue
        try:
            text = Path(f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for kind, code in H.test_codes(text):
            if kind == "arc":
                if code not in arc_codes:
                    errors.append(("test", f"{f}: `{code}` non esiste in {arc_doc.name}"))
            else:
                if req_codes is None:
                    req_codes = load_req_codes(product)
                if code not in req_codes:
                    errors.append(("test", f"{f}: `{code}` non esiste nel documento Requisiti di Linear"))

    # 5. FROM pinnati nei Dockerfile toccati (ADR 0005, CHK-019)
    for f in changed:
        name = Path(f).name
        if not (name == "Dockerfile" or name.startswith("Dockerfile.") or name.endswith(".Dockerfile")):
            continue
        if not Path(f).is_file():
            continue
        for p in H.check_dockerfile(Path(f).read_text(encoding="utf-8", errors="replace")):
            errors.append(("dockerfile", f"{f}: {p}"))

    lines = [
        "### pr-checks",
        "",
        f"PR #{pr} · branch `{branch}` · autore `{author}`",
        "",
        "| controllo | esito |",
        "|---|---|",
    ]
    checks = ["branch", "closes", "definizione di fatto", "test", "dockerfile", "arc"]
    for c in checks:
        ko = [m for k, m in errors if k == c]
        lines.append(f"| {c} | {'❌ ' + '; '.join(ko) if ko else '✅'} |")
    if links:
        lines.append("")
        lines.append("collegamenti: " + ", ".join(f"{rel} {iss}" for rel, iss in links))
    H.summary("\n".join(lines))

    for k, m in errors:
        print(f"::error::{k}: {m}")
    if errors:
        sys.exit(1)
    print("pr-checks: tutto in regola")


def load_req_codes(product: dict) -> set[str]:
    ref = product.get("linear_progetto")
    if not ref:
        H.fail("product.yaml: manca `linear_progetto`, serve per verificare i codici REQ- dei test")
    project = H.linear_project(ref)
    docs = H.linear_documents(project["id"])
    return set(H.parse_requisiti(H.linear_document(docs, "Requisiti")))


if __name__ == "__main__":
    main()
