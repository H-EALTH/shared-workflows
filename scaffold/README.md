# Scaffold di un prodotto

File da copiare in un repository prodotto nuovo (o da confrontare con `app-web`). Si sostituisce `SO`
con il codice del prodotto e `so-ulss2` con il prefisso del tag.

| File | Cosa fa |
|---|---|
| `product.yaml` | codice, prefisso del tag, copertura minima, progetto Linear (`discover`) |
| `app/<componente>/component.yaml` | genere e codice ARC- del componente |
| `.github/workflows/ci.yml` | CI: discover, pr-checks, lint, test, scan, build, e2e, ci-ok |
| `.github/workflows/release.yml` | CD: promote, test-evidence, soup-evidence, traceability, release |
| `.github/workflows/draft-docs.yml` | bozze dei documenti QMS dopo la Release |
| `.github/PULL_REQUEST_TEMPLATE.md` | collegamento alla sotto-issue e definizione di fatto (pr-checks) |
| `.github/dependabot.yml` | aggiornamenti di shared-workflows, immagini base, pip, npm |
| `CODEOWNERS` | review del team engineering |
| `docs/architecture/SO-ARC-001.md` | copia della tabella dei componenti ARC- (discover, pr-checks, traceability) |
| `docs/SO-REC-001_Lista-SOUP.csv` | lista SOUP del prodotto (soup-evidence, CHK-021) |
| `tests/system/` | compose, dati sintetici e test di sistema `test_req_nnn_...` (e2e) |

Secret del repository: `LINEAR_API_KEY` (pr-checks, traceability), `ANTHROPIC_API_KEY` (draft-docs).
