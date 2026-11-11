"""collect-release-notes: pull-requests.csv (allegato 3) e notes.md (corpo della Release candidate).

Variabili: PRODUCT (JSON), TAG, ARTIFACTS (file), OUT (cartella), GH_TOKEN, GITHUB_REPOSITORY,
GITHUB_SHA. Le pull request sono quelle i cui commit stanno fra il tag precedente e questo
(`compare`), qualunque sia il branch di fusione (dev, main per gli hotfix).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

HEADER = ["numero", "titolo", "autore", "approvatori", "fusa_il", "branch", "issue", "url"]


def previous_tag(prefix: str, tag: str) -> str | None:
    r = subprocess.run(
        ["git", "tag", "--list", f"{prefix}-v*", "--sort=-v:refname"], capture_output=True, text=True, check=True
    )
    tags = [t for t in r.stdout.split() if re.fullmatch(re.escape(prefix) + r"-v\d+\.\d+\.\d+", t) and t != tag]
    # il tag precedente è il più alto fra quelli raggiungibili dal commit taggato
    for t in tags:
        ok = subprocess.run(["git", "merge-base", "--is-ancestor", t, os.environ["GITHUB_SHA"]]).returncode == 0
        if ok:
            return t
    return None


def main() -> None:
    product = json.loads(os.environ["PRODUCT"])
    tag, repo, sha = os.environ["TAG"], os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"]
    out = Path(os.environ["OUT"])
    artifacts = Path(os.environ["ARTIFACTS"]).read_text(encoding="utf-8").split()
    prev = previous_tag(product["tag"], tag)

    if prev:
        commits = H.gh_api(f"repos/{repo}/compare/{prev}...{sha}", paginate=False).get("commits", [])
        shas = [c["sha"] for c in commits]
    else:
        shas = subprocess.run(["git", "rev-list", sha], capture_output=True, text=True, check=True).stdout.split()

    prs: dict[int, dict] = {}
    for s in shas:
        for p in H.gh_api(f"repos/{repo}/commits/{s}/pulls"):
            if p.get("merged_at") and p["number"] not in prs:
                prs[p["number"]] = p
    rows = []
    for n, p in sorted(prs.items()):
        reviews = H.gh_api(f"repos/{repo}/pulls/{n}/reviews")
        approvers = sorted({r["user"]["login"] for r in reviews if r.get("state") == "APPROVED" and r.get("user")})
        links = " ".join(f"{rel} {iss}" for rel, iss in H.pr_links(p.get("body") or ""))
        rows.append(
            [
                n,
                p["title"],
                p["user"]["login"],
                " ".join(approvers),
                p["merged_at"],
                p["head"]["ref"],
                links,
                p["html_url"],
            ]
        )
    H.write_csv(out / "pull-requests.csv", HEADER, rows)

    notes = [
        f"## Versione candidata `{tag}`",
        "",
        f"Commit `{sha}` · versione precedente: `{prev or 'nessuna'}` · {len(rows)} pull request fuse.",
        "",
        "Un tag non è una messa in esercizio (HE-SOP-004 par. 4.1): la versione è candidata finché il",
        "documento di messa in esercizio (HE-TPL-006) non è firmato. Gli allegati qui sotto sono le",
        "registrazioni generate dalla pipeline da allegare a quel documento.",
        "",
        "## Artefatti (il prodotto è la lista dei digest)",
        "",
    ]
    notes += [f"- `{a}`" for a in artifacts]
    notes += ["", "## Pull request fuse", "", "| # | titolo | autore | approvatori | issue |", "|---|---|---|---|---|"]
    notes += [
        f"| [#{r[0]}]({r[7]}) | {r[1]} | @{r[2]} | {' '.join('@' + a for a in r[3].split()) or '-'} | {r[6] or '-'} |"
        for r in rows
    ]
    notes += [
        "",
        "## Allegati",
        "",
        "- `test-report.csv`, `coverage.csv` (allegato 1 di HE-TPL-006)",
        "- `<PROD>-REC-002_Matrice-tracciabilita.csv`, `UserNeed_*.md`, `Requisiti_*.md` (allegato 2)",
        "- `pull-requests.csv` (allegato 3)",
        "- `artifacts.txt`, `sbom-<comp>.spdx.json` (allegato 4)",
        "- `scan-report.csv`, `<PROD>-REC-001_Lista-SOUP.csv`, `soup-diff.csv` (allegato 5, HE-TPL-006 par. 6)",
        f"- `bundle-{tag}.zip`: tutti gli allegati in un unico archivio",
    ]
    (out / "notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    H.summary(f"### collect-release-notes\n\n{len(rows)} pull request fuse da `{prev or 'inizio'}` a `{tag}`")


if __name__ == "__main__":
    main()
