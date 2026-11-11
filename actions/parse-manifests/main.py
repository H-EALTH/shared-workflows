"""parse-manifests: legge product.yaml e i component.yaml, verifica le convenzioni e restituisce la matrix.

Uscite (GITHUB_OUTPUT): `product` (JSON di product.yaml) e `components` (JSON: lista di name, path,
kind, arc, ordinata per path). I manifest sono YAML piatto (`chiave: valore`): li legge un parser
minimo di sola libreria standard; annidamenti, liste e chiavi ripetute fanno fallire. Tutti gli errori
sono riportati insieme, ognuno con file e causa.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_lib"))
import helib as H  # noqa: E402

PRODUCT_KEYS = ("codice", "tag", "copertura_minima", "linear_progetto")
COMPONENT_KEYS = ("kind", "arc")
REQUIRED_FILES = {
    "python": ("Dockerfile", "pyproject.toml", "requirements-dev.txt"),
    "node": ("Dockerfile", "package.json", "package-lock.json"),
}
RE_CODICE = re.compile(r"^[A-Z][A-Z0-9]*$")
RE_TAG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RE_NAME = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")  # nome di immagine valido su GHCR
RE_ARC_CODE = re.compile(r"^ARC-\d{3}$")
SKIP_DIRS = {"node_modules", "venv", "__pycache__"}


def strip_comment(line: str) -> str:
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            return line[:i]
    return line


def flat_yaml(path: Path, errors: list[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = strip_comment(raw).rstrip()
        if not line.strip() or line.strip() == "---":
            continue
        m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)", line)
        if not m or line[0].isspace():
            errors.append(f"{path}:{n}: atteso `chiave: valore` al primo livello, senza annidamenti né liste")
            continue
        key, value = m.group(1), m.group(2).strip()
        if value[:1] in ("{", "[", "|", ">", "&", "*", ""):
            errors.append(f"{path}:{n}: `{key}` deve avere un valore semplice su una riga")
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key in data:
            errors.append(f"{path}:{n}: chiave `{key}` ripetuta")
        data[key] = value
    return data


def check_keys(path: Path, data: dict[str, str], expected: tuple[str, ...], errors: list[str]) -> None:
    missing = [k for k in expected if k not in data]
    extra = sorted(k for k in data if k not in expected)
    if missing:
        errors.append(f"{path}: mancano le chiavi {', '.join(missing)}")
    if extra:
        errors.append(f"{path}: chiavi non previste {', '.join(extra)} (ammesse: {', '.join(expected)})")


def read_product(errors: list[str]) -> dict:
    path = Path("product.yaml")
    if not path.is_file():
        errors.append("product.yaml assente nella radice del repository")
        return {}
    data = flat_yaml(path, errors)
    check_keys(path, data, PRODUCT_KEYS, errors)
    product: dict = dict(data)
    if "codice" in data and not RE_CODICE.match(data["codice"]):
        errors.append(f"{path}: `codice` '{data['codice']}' deve essere maiuscolo, es. SO")
    if "tag" in data and not RE_TAG.match(data["tag"]):
        errors.append(f"{path}: `tag` '{data['tag']}' deve essere minuscolo con trattini, es. so-ulss2")
    if "copertura_minima" in data:
        try:
            cov = int(data["copertura_minima"])
            if not 0 <= cov <= 100:
                raise ValueError
            product["copertura_minima"] = cov
        except ValueError:
            errors.append(f"{path}: `copertura_minima` '{data['copertura_minima']}' deve essere un intero da 0 a 100")
    if "linear_progetto" in data and not data["linear_progetto"].strip():
        errors.append(f"{path}: `linear_progetto` vuoto")
    return product


def find_manifests() -> list[Path]:
    found = []
    for p in Path(".").rglob("component.yaml"):
        parts = p.parts[:-1]
        if any(x.startswith(".") or x in SKIP_DIRS for x in parts):
            continue
        found.append(p)
    return sorted(found, key=lambda p: p.as_posix())


def read_components(codice: str, errors: list[str]) -> list[dict[str, str]]:
    arc_doc = Path("docs/architecture") / f"{codice}-ARC-001.md"
    arc_codes: set[str] | None = None
    if codice:
        if arc_doc.is_file():
            arc_codes = H.parse_arc_codes(arc_doc.read_text(encoding="utf-8"))
        else:
            errors.append(f"{arc_doc} assente: serve per verificare gli `arc` dei component.yaml")

    components: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for manifest in find_manifests():
        folder = manifest.parent
        if folder == Path("."):
            errors.append("component.yaml nella radice: ogni componente sta in una sua cartella")
            continue
        name, path = folder.name, folder.as_posix()
        data = flat_yaml(manifest, errors)
        check_keys(manifest, data, COMPONENT_KEYS, errors)
        if not RE_NAME.match(name):
            errors.append(f"{manifest}: il nome della cartella '{name}' deve essere minuscolo (a-z, 0-9, . _ -)")
        if name in seen:
            errors.append(f"{manifest}: nome '{name}' già usato da {seen[name]}")
        seen.setdefault(name, path)
        kind, code = data.get("kind", ""), data.get("arc", "")
        if "kind" in data and kind not in REQUIRED_FILES:
            errors.append(f"{manifest}: `kind` '{kind}' non ammesso (ammessi: {', '.join(REQUIRED_FILES)})")
        for f in REQUIRED_FILES.get(kind, ()):
            if not (folder / f).is_file():
                errors.append(f"{manifest}: manca {path}/{f}, obbligatorio per kind {kind}")
        if "arc" in data:
            if not RE_ARC_CODE.match(code):
                errors.append(f"{manifest}: `arc` '{code}' non è nel formato ARC-nnn")
            elif arc_codes is not None and code not in arc_codes:
                errors.append(f"{manifest}: `arc` {code} non è nella tabella dei componenti di {arc_doc}")
        components.append({"name": name, "path": path, "kind": kind, "arc": code})
    if not components and not errors:
        errors.append("nessun component.yaml trovato: ogni componente ne ha uno nella sua cartella")
    return components


def main() -> None:
    errors: list[str] = []
    product = read_product(errors)
    codice = product.get("codice", "")
    components = read_components(codice if RE_CODICE.match(codice) else "", errors)

    if errors:
        for e in errors:
            print(f"::error::{e}")
        H.summary("### parse-manifests\n\n" + "\n".join(f"- ❌ {e}" for e in errors))
        sys.exit(1)

    H.set_output("product", json.dumps(product, ensure_ascii=False))
    H.set_output("components", json.dumps(components, ensure_ascii=False))
    lines = [
        "### parse-manifests",
        "",
        f"Prodotto `{product['codice']}` · tag `{product['tag']}-vX.Y.Z` · copertura minima {product['copertura_minima']}%",
        "",
        "| componente | cartella | kind | arc |",
        "|---|---|---|---|",
    ]
    lines += [f"| {c['name']} | `{c['path']}` | {c['kind']} | {c['arc']} |" for c in components]
    H.summary("\n".join(lines))


if __name__ == "__main__":
    main()
