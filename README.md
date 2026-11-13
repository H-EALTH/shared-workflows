# shared-workflows

Workflow GitHub Actions e action riutilizzabili per la CI/CD dei prodotti H-EALTH. I prodotti li chiamano
con il tag completo: `H-EALTH/shared-workflows/.github/workflows/<stazione>.yml@v0.0.1`.

Come si usano: [docs/ci.md](docs/ci.md) (CI) e [docs/cd.md](docs/cd.md) (release e deploy).

## Workflow

Tutti `on: workflow_call`, tranne `check.yml`.

| Workflow | Flusso | Cosa fa |
|---|---|---|
| `discover.yml` | CI, release | legge `product.yaml` e i `component.yaml`, verifica le convenzioni, produce la matrix |
| `pr-checks.yml` | CI (PR) | branch, Closes/Part of, definizione di fatto, codici dei test, FROM pinnati |
| `lint.yml` | CI | ruff + mypy (python), eslint + tsc (node) |
| `test.yml` | CI | tests/unit + tests/integration, JUnit, copertura con soglia |
| `scan.yml` | CI | Trivy sul filesystem: vulnerabilità con fix, segreti, misconfig |
| `build.yml` | CI (push) | immagine locale → contenuto, Trivy, SBOM → push su GHCR `sha-<short>` |
| `verify.yml` | CI (push) | compose con le immagini per digest, dati sintetici, tests/system |
| `promote.yml` | release | tag conforme e su `main`, run ci verde, tag di versione sugli stessi digest |
| `qms-records.yml` | release | registrazioni di HE-TPL-006 dal run ci: `test-report`, `soup`, `traceability` |
| `publish.yml` | release | `pull-requests.csv`, Release «candidate» con tutti gli allegati |
| `resolve.yml` | deploy | Release del tag e il suo `artifacts.txt`, restituisce le immagini per digest |
| `install.yml` | deploy | su un runner self-hosted: digest nell'overlay kustomize, `kubectl apply`, attesa del rollout |
| `check.yml` | - | CI di questo repository: actionlint, ruff, pin interni |

## Action

In `actions/`, composite, Python 3.12 di sola libreria standard (libreria comune in `actions/_lib/helib.py`).

| Action | Usata da | Output |
|---|---|---|
| `parse-manifests` | `discover.yml` | `product`, `components` (JSON) |
| `validate-pr` | `pr-checks.yml` | esito del job |
| `collect-test-evidence` | `qms-records.yml` (`test-report`) | `test-report.csv`, `coverage.csv` |
| `build-soup-list` | `qms-records.yml` (`soup`) | `scan-report.csv`, `<PROD>-REC-001_Lista-SOUP.csv`, `soup-diff.csv` |
| `build-traceability-matrix` | `qms-records.yml` (`traceability`) | `<PROD>-REC-002_Matrice-tracciabilita.csv`, `UserNeed_*.md`, `Requisiti_*.md` |
| `collect-release-notes` | `publish.yml` | `pull-requests.csv`, corpo della Release |
