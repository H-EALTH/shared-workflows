"""draft-docs: bozze QMS dal bundle della Release, con le skill di skills/ e i template di qms/templates/.

Variabili: PRODUCT (JSON), TAG, BUNDLE, OUT (cartelle), INFRA_CHANGED (true/false), MODEL, ROOT
(radice di shared-workflows), ANTHROPIC_API_KEY, GITHUB_REPOSITORY, GITHUB_SERVER_URL.

Il modello vede solo: il template, la skill, il contenuto del bundle (CSV, artifacts.txt, export
Linear) e i metadati della Release. Niente codice, niente dati di paziente (HE-SOP-012 par. 3).
"""

import csv
import io
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

MAX_CHARS = 60_000  # per file del bundle, dopo di che si tronca con avviso

RULES = """Sei uno strumento del sistema di gestione della qualità di H-EALTH (ISO 13485, IEC 62304).
Scrivi in italiano, nello stile dei documenti del sistema: frasi corte, nessun trattino lungo, nessun
punto intermedio, nessun campo vuoto. Compili il modello fornito con i soli dati forniti: non inventi
nulla. Ogni informazione che non è nei dati, o che richiede un giudizio umano (esiti sì/no, valutazioni,
firme, date di riunione, nomi di persone, decisioni), la scrivi esattamente come `[DA COMPILARE: ruolo]`,
dove ruolo è chi deve deciderla (responsabile tecnico e regolatorio, product manager, responsabile
tecnico, direzione). Conservi i titoli e l'ordine dei paragrafi del modello. Elimini il riquadro
«Come si usa». Il front-matter del documento ha `stato: bozza`, `generato_da: draft-docs`,
`versione: <x.y.z>` e `data: <oggi>`. Rispondi con il solo documento markdown, senza commenti."""


def read_bundle(bundle: Path) -> dict[str, str]:
    files = {}
    for p in sorted(bundle.rglob("*")):
        if not p.is_file() or p.suffix not in {".csv", ".txt", ".md"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + f"\n[... troncato a {MAX_CHARS} caratteri ...]\n"
        files[p.name] = text
    return files


def rows(files: dict[str, str], name: str) -> list[dict[str, str]]:
    text = next((v for k, v in files.items() if k == name or k.endswith(name)), None)
    return list(csv.DictReader(io.StringIO(text))) if text else []


def call_model(system: str, user: str, model: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        H.fail("ANTHROPIC_API_KEY mancante")
    body = json.dumps(
        {"model": model, "max_tokens": 8000, "system": system, "messages": [{"role": "user", "content": user}]}
    ).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read().decode())
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def ensure_front_matter(md: str, version: str) -> str:
    md = md.strip()
    if md.startswith("```"):
        md = re.sub(r"^```[a-z]*\n|\n```$", "", md).strip()
    if not md.startswith("---"):
        md = (
            f"---\nstato: bozza\ngenerato_da: draft-docs\nversione: {version}\ndata: {date.today().isoformat()}\n---\n\n"
            + md
        )
    elif "stato: bozza" not in md.split("---", 2)[1]:
        md = md.replace("---", "---\nstato: bozza", 1)
    return md + "\n"


def main() -> None:
    product = json.loads(os.environ["PRODUCT"])
    tag, model = os.environ["TAG"], os.environ["MODEL"]
    bundle, out, root = Path(os.environ["BUNDLE"]), Path(os.environ["OUT"]), Path(os.environ["ROOT"]).resolve()
    infra_changed = os.environ.get("INFRA_CHANGED", "false").lower() == "true"
    codice, prod = product["codice"], product["tag"]
    version = tag.rsplit("-v", 1)[-1]
    out.mkdir(parents=True, exist_ok=True)
    files = read_bundle(bundle)
    if not files:
        H.fail(f"bundle vuoto in {bundle}")

    matrix = rows(files, "REC-002_Matrice-tracciabilita.csv")
    prs = {r["numero"] for r in rows(files, "pull-requests.csv")}
    rc_touched = sorted(
        {
            c
            for r in matrix
            if r.get("rc") and any(p.lstrip("#") in prs for p in r.get("pull_request", "").split())
            for c in r["rc"].split()
        }
    )

    context = [
        f"# Dati della versione\n\nprodotto: {codice} ({prod}) · tag: {tag} · versione: {version} · "
        f"repository: {os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY', '')} · "
        f"data: {date.today().isoformat()}\n"
    ]
    for name, text in files.items():
        context.append(f"## File `{name}`\n\n```\n{text}\n```\n")
    data = "\n".join(context)

    def skill(name: str) -> str:
        return (root / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def template(prefix: str) -> str:
        matches = sorted((root / "qms" / "templates").glob(f"{prefix}_*.md"))
        if not matches:
            H.fail(f"template {prefix} assente in qms/templates/")
        return matches[-1].read_text(encoding="utf-8")

    plan = [
        ("messa-in-esercizio", "HE-TPL-006", f"MessaInEsercizio_{prod}_{version}.md"),
        ("rapporto-prova", "HE-TPL-024", f"Prova_manuale_{version}_{date.today().isoformat()}.md"),
    ]
    if infra_changed:
        plan.append(("descrizione-tecnica", "HE-TPL-022", f"Proposta_{codice}-DTE-001_{version}.md"))
    if rc_touched:
        plan.append(("istruzioni-uso", "HE-TPL-021", f"Proposta_{codice}-IFU-001_{version}.md"))

    produced = []
    for skill_name, tpl, filename in plan:
        system = RULES + "\n\n# Skill\n\n" + skill(skill_name)
        extra = ""
        if skill_name == "istruzioni-uso":
            extra = (
                "\n\n# Misure di controllo del rischio toccate da questa versione\n\n" + ", ".join(rc_touched) + "\n"
            )
        if skill_name == "descrizione-tecnica":
            extra = "\n\n# Nota\n\nIl diff dal tag precedente tocca la cartella infra/.\n"
        user = f"# Modello {tpl}\n\n{template(tpl)}\n\n{data}{extra}"
        md = ensure_front_matter(call_model(system, user, model), version)
        (out / filename).write_text(md, encoding="utf-8")
        produced.append(filename)
        print(f"scritto {filename} ({len(md)} caratteri)")

    (out / "README.md").write_text(
        f"# draft-docs {tag}\n\nBozze generate il {date.today().isoformat()} con il modello `{model}` dal bundle della "
        f"Release. Sono proposte: ogni campo `[DA COMPILARE: ruolo]` richiede una decisione umana e il documento "
        f"resta `stato: bozza` finché non è compilato, riesaminato e firmato secondo HE-SOP-001.\n\n"
        + "\n".join(f"- `{f}`" for f in produced)
        + ("\n\nNessuna proposta DTE-001: il diff non tocca infra/." if not infra_changed else "")
        + ("\n\nNessuna proposta IFU-001: nessuna misura RC- toccata." if not rc_touched else ""),
        encoding="utf-8",
    )
    H.summary("### draft-docs\n\n" + "\n".join(f"- `{f}`" for f in produced))


if __name__ == "__main__":
    main()
