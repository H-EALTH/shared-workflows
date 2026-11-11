"""build-soup-list: scan-report.csv, <PROD>-REC-001_Lista-SOUP.csv aggiornata, soup-diff.csv.

Variabili: COMPONENTS, PRODUCT (JSON), EVIDENCE, SBOM, OUT (cartelle), TAG.
Regole (HE-SOP-004 par. 3.1): la pipeline genera il punto 1 (nome, produttore, versione) dai file di
dipendenza diretti (requirements.txt, pyproject.toml, package.json, FROM dei Dockerfile); le
dipendenze transitive non entrano. I punti da 2 a 7 restano a mano: la lista committata deve avere
una riga per ogni componente generato e nessuna riga in più (CHK-021), salvo le righe segnaposto
con versione `DA DEFINIRE` o vuota.
"""

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

SCAN_HEADER = [
    "componente",
    "report",
    "target",
    "kind",
    "severity",
    "id",
    "package",
    "installed",
    "fixed",
    "status",
    "title",
    "url",
]
DIFF_HEADER = ["componente", "da_versione", "a_versione", "variazione", "usato_da"]


def norm_key(name: str) -> str:
    """Chiave di confronto: minuscolo, prima della parentesi, `_` come `-`."""
    return re.sub(r"[_.]", "-", name.split("(")[0].strip().lower())


def pyname(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


# --- report Trivy --------------------------------------------------------------------------


def scan_rows(evidence: Path, components: list[dict]) -> list[list[str]]:
    rows, missing = [], []
    for c in components:
        for kind in ("fs", "image"):
            suffix = "" if kind == "fs" else "-image"
            src = evidence / f"scan-{c['name']}{suffix}" / f"scan-{c['name']}{suffix}.json"
            if not src.is_file():
                missing.append(str(src))
                continue
            rep = json.loads(src.read_text(encoding="utf-8"))
            for r in rep.get("Results") or []:
                t = r.get("Target", "")
                for v in r.get("Vulnerabilities") or []:
                    rows.append(
                        [
                            c["name"],
                            kind,
                            t,
                            "vulnerability",
                            v.get("Severity", ""),
                            v.get("VulnerabilityID", ""),
                            v.get("PkgName", ""),
                            v.get("InstalledVersion", ""),
                            v.get("FixedVersion", ""),
                            v.get("Status", ""),
                            (v.get("Title") or "")[:80],
                            v.get("PrimaryURL", ""),
                        ]
                    )
                for s in r.get("Secrets") or []:
                    rows.append(
                        [
                            c["name"],
                            kind,
                            t,
                            "secret",
                            s.get("Severity", ""),
                            s.get("RuleID", ""),
                            "",
                            "",
                            "",
                            f"riga {s.get('StartLine')}",
                            s.get("Title", ""),
                            "",
                        ]
                    )
                for m in r.get("Misconfigurations") or []:
                    rows.append(
                        [
                            c["name"],
                            kind,
                            t,
                            "misconfig",
                            m.get("Severity", ""),
                            m.get("ID", ""),
                            "",
                            "",
                            "",
                            m.get("Status", ""),
                            (m.get("Title") or "")[:80],
                            m.get("PrimaryURL", ""),
                        ]
                    )
    if missing:
        H.fail("report Trivy attesi e non trovati nel run ci: " + ", ".join(missing))
    return rows


# --- SBOM -------------------------------------------------------------------------------------


def sbom_index(sbom_dir: Path, comp: str) -> dict[tuple[str, str], tuple[str, str]]:
    """{(tipo, nome normalizzato): (versione, fornitore)} dalla SBOM SPDX del componente."""
    src = sbom_dir / f"sbom-{comp}.spdx.json"
    if not src.is_file():
        H.fail(f"manca {src} (job promote)")
    doc = json.loads(src.read_text(encoding="utf-8"))
    idx: dict[tuple[str, str], tuple[str, str]] = {}
    for p in doc.get("packages", []):
        purl = next((e["referenceLocator"] for e in p.get("externalRefs", []) if e.get("referenceType") == "purl"), "")
        ptype = purl.split("/")[0].removeprefix("pkg:") if purl else ""
        supplier = p.get("supplier") or ""
        supplier = "" if supplier.upper() == "NOASSERTION" else re.sub(r"^(Organization|Person):\s*", "", supplier)
        key = (ptype, pyname(p.get("name", "")) if ptype == "pypi" else p.get("name", "").lower())
        idx.setdefault(key, (p.get("versionInfo", ""), supplier))
    return idx


# --- dipendenze dirette ---------------------------------------------------------------------------


def dockerfile_bases(path: Path) -> list[dict]:
    out, stages = [], set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
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
        repo, _, digest = ref.partition("@")
        repo, _, tag = repo.partition(":")
        name = repo.rsplit("/", 1)[-1]
        namespace = repo.rsplit("/", 1)[0] if "/" in repo else "library"
        version = (tag or "latest") + (f"@{digest}" if digest else "")
        out.append({"componente": name, "produttore": namespace, "versione": version, "tipo": "immagine"})
    return out


def python_deps(path: Path, sbom: dict) -> list[dict]:
    names: dict[str, str] = {}  # nome → versione pinnata o ""
    req = path / "requirements.txt"
    if req.is_file():
        for line in req.read_text(encoding="utf-8").splitlines():
            s = line.split("#", 1)[0].strip()
            if not s or s.startswith("-"):
                continue
            m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(==\s*([^\s;]+))?", s)
            if m:
                names.setdefault(pyname(m.group(1)), m.group(4) or "")
    pyproject = path / "pyproject.toml"
    if pyproject.is_file():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        for dep in data.get("project", {}).get("dependencies", []) or []:
            m = re.match(r"([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?\s*(==\s*([^\s;,]+))?", dep)
            if m:
                names.setdefault(pyname(m.group(1)), m.group(4) or "")
    out = []
    for name, pinned in sorted(names.items()):
        version, supplier = sbom.get(("pypi", name), ("", ""))
        out.append({"componente": name, "produttore": supplier, "versione": pinned or version, "tipo": "pypi"})
    return out


def node_deps(path: Path, sbom: dict) -> list[dict]:
    pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
    lock_path = path / "package-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else {}
    packages = lock.get("packages", {})
    out = []
    for name in sorted((pkg.get("dependencies") or {}).keys()):
        version = (packages.get(f"node_modules/{name}") or {}).get("version", "")
        sb_version, supplier = sbom.get(("npm", name.lower()), ("", ""))
        out.append({"componente": name, "produttore": supplier, "versione": version or sb_version, "tipo": "npm"})
    return out


def generated_list(components: list[dict], sbom_dir: Path) -> dict[str, dict]:
    """{chiave: {componente, produttore, versione, tipo, usato_da}} di tutte le dipendenze dirette."""
    merged: dict[str, dict] = {}
    for c in components:
        path = Path(c["path"])
        sbom = sbom_index(sbom_dir, c["name"])
        items = dockerfile_bases(path / "Dockerfile") if (path / "Dockerfile").is_file() else []
        if c["kind"] == "python":
            items += python_deps(path, sbom)
        elif c["kind"] == "node":
            items += node_deps(path, sbom)
        for it in items:
            key = norm_key(it["componente"])
            cur = merged.setdefault(key, {**it, "usato_da": []})
            if it["versione"] and not cur["versione"]:
                cur["versione"] = it["versione"]
            if it["produttore"] and not cur["produttore"]:
                cur["produttore"] = it["produttore"]
            if c["name"] not in cur["usato_da"]:
                cur["usato_da"].append(c["name"])
    return merged


# --- lista SOUP committata ---------------------------------------------------------------------------


def is_placeholder(row: dict[str, str]) -> bool:
    v = (row.get("versione") or "").strip().upper()
    return v == "" or v.startswith("DA DEFINIRE") or "NON E' SOUP" in (row.get("funzione_nel_prodotto") or "").upper()


def git_show(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def previous_tag(prefix: str, tag: str) -> str | None:
    r = subprocess.run(
        ["git", "tag", "--list", f"{prefix}-v*", "--sort=-v:refname"], capture_output=True, text=True, check=True
    )
    tags = [t for t in r.stdout.split() if re.fullmatch(re.escape(prefix) + r"-v\d+\.\d+\.\d+", t)]
    if tag in tags:
        i = tags.index(tag)
        return tags[i + 1] if i + 1 < len(tags) else None
    return tags[0] if tags else None


def main() -> None:
    components = json.loads(os.environ["COMPONENTS"])
    product = json.loads(os.environ["PRODUCT"])
    evidence, sbom_dir, out = Path(os.environ["EVIDENCE"]), Path(os.environ["SBOM"]), Path(os.environ["OUT"])
    tag = os.environ["TAG"]
    codice = product["codice"]
    rec_path = f"docs/{codice}-REC-001_Lista-SOUP.csv"

    # allegato 5
    H.write_csv(out / "scan-report.csv", SCAN_HEADER, scan_rows(evidence, components))

    # punto 1 della lista SOUP, generato
    gen = generated_list(components, sbom_dir)

    # confronto con la lista committata (CHK-021)
    if not Path(rec_path).is_file():
        H.fail(f"manca {rec_path}: la lista SOUP del prodotto va committata (HE-SOP-004 par. 3.1)")
    header, rows = H.read_csv(rec_path)
    for col in ("componente", "produttore", "versione"):
        if col not in header:
            H.fail(f"{rec_path}: manca la colonna `{col}`")
    rec_keys = {norm_key(r["componente"]): r for r in rows if not is_placeholder(r)}
    placeholders = [r["componente"] for r in rows if is_placeholder(r)]
    missing_rows = sorted(k for k in gen if k not in rec_keys)
    extra_rows = sorted(k for k in rec_keys if k not in gen)
    errors = []
    if missing_rows:
        errors.append(
            "dipendenze senza riga nella lista SOUP (compilare i punti 2-7): "
            + ", ".join(gen[k]["componente"] for k in missing_rows)
        )
    if extra_rows:
        errors.append(
            "righe della lista SOUP senza dipendenza nei file del repository (togliere o marcare "
            "`DA DEFINIRE`): " + ", ".join(rec_keys[k]["componente"] for k in extra_rows)
        )

    # lista aggiornata nelle colonne deterministiche
    updated = []
    for r in rows:
        r = dict(r)
        g = gen.get(norm_key(r["componente"]))
        if g and not is_placeholder(r):
            if g["versione"]:
                r["versione"] = g["versione"]
            if g["produttore"] and (
                not r["produttore"].strip() or r["produttore"].strip().upper().startswith("DA COMPILARE")
            ):
                r["produttore"] = g["produttore"]
        updated.append(r)
    for k in missing_rows:
        g = gen[k]
        updated.append(
            {h: "" for h in header}
            | {
                "componente": g["componente"],
                "produttore": g["produttore"],
                "versione": g["versione"],
                "note": "AGGIUNTA DALLA PIPELINE: compilare i punti 2-7",
            }
        )
    H.write_csv(out / f"{codice}-REC-001_Lista-SOUP.csv", header, updated)

    # differenza rispetto al tag precedente
    prev = previous_tag(product["tag"], tag)
    prev_rows: dict[str, dict] = {}
    if prev:
        text = git_show(prev, rec_path)
        if text:
            tmp = out / ".prev-soup.csv"
            tmp.write_text(text, encoding="utf-8")
            _, prows = H.read_csv(tmp)
            tmp.unlink()
            prev_rows = {norm_key(r["componente"]): r for r in prows if not is_placeholder(r)}
    diff = []
    for k, g in sorted(gen.items()):
        before = (prev_rows.get(k) or {}).get("versione", "")
        if k not in prev_rows:
            diff.append([g["componente"], "", g["versione"], "aggiunto", " ".join(g["usato_da"])])
        elif before != g["versione"]:
            diff.append([g["componente"], before, g["versione"], "aggiornato", " ".join(g["usato_da"])])
    for k, r in sorted(prev_rows.items()):
        if k not in gen:
            diff.append([r["componente"], r.get("versione", ""), "", "rimosso", ""])
    H.write_csv(out / "soup-diff.csv", DIFF_HEADER, diff)

    lines = [
        "### build-soup-list",
        "",
        f"{len(gen)} componenti di terzi diretti · lista committata `{rec_path}` con {len(rows)} righe"
        + (f" ({len(placeholders)} segnaposto)" if placeholders else ""),
        f"differenza rispetto a `{prev or '(nessun tag precedente)'}`: {len(diff)} variazioni",
        "",
    ]
    if diff:
        lines += ["| componente | da | a | variazione |", "|---|---|---|---|"]
        lines += [f"| {d[0]} | {d[1]} | {d[2]} | {d[3]} |" for d in diff]
    H.summary("\n".join(lines))
    for e in errors:
        print(f"::error::CHK-021: {e}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
