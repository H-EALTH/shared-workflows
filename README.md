# shared-workflows

Workflow GitHub Actions e action riutilizzabili per la CI/CD dei prodotti H-EALTH.

Versione di riferimento: `H-EALTH/shared-workflows@v0.5.0`. I prodotti pinnano il tag completo:
`H-EALTH/shared-workflows/.github/workflows/<stazione>.yml@vX.Y.Z`.

`shared-workflows` contiene i workflow riusabili e le action che ogni prodotto H-EALTH chiama per
verificare, costruire, provare e rilasciare i propri componenti, e per produrre le registrazioni che il
sistema di gestione richiede. È una catena di montaggio a stazioni: il prodotto non scrive logica di
CI, dichiara sé stesso (`product.yaml`) e i suoi componenti (`component.yaml`) e chiama le stazioni.

## Flussi

| Flusso | Quando parte | Documento |
|---|---|---|
| CI del prodotto | ogni PR verso `dev` e `main`, ogni push su `dev` e `main` | [ci.md](docs/ci.md): `product.yaml`, `component.yaml`, i sette job più il gate, cosa fare quando una stazione fallisce |
| Rilascio del prodotto | push di un tag `<prefix>-vX.Y.Z` | [release.md](docs/release.md): tag, versione candidata, le cinque stazioni, gli allegati di HE-TPL-006 |
| Bozze dei documenti QMS | dopo il rilascio, workflow separato | [release.md](docs/release.md#draft-docs): segnaposto `draft-docs` |
| Rilascio di `shared-workflows` | nuova versione dei workflow riusabili | [versionamento.md](docs/versionamento.md): tag, numerazione, pin interni |

## Principi

- **Un componente, un artefatto, un digest.** Ogni componente produce un'immagine immutabile su GHCR,
  identificata dal digest `sha256:…`. Il rilascio è la lista dei digest.
- **Il prodotto e i componenti si dichiarano.** `product.yaml` nella radice, `component.yaml` in ogni
  cartella componente. La struttura delle cartelle la decide il prodotto.
- **Una stazione, una responsabilità.** Chi verifica non costruisce, chi costruisce non rilascia, chi
  rilascia non costruisce. Le prove nascono dove si producono e si recuperano, non si rifanno.
- **Un'immagine esiste solo se è passata dai controlli.** Contenuto, Trivy e SBOM prima del push; il tag
  di versione si aggiunge ai digest già provati.
- **La pipeline conosce il prodotto come lo conosce il QMS.** Stessi codici (`REQ-`, `ARC-`, `RC-`,
  `<PROD>-REC-001`, `<PROD>-REC-002`), stesse fonti (documenti Linear, nomi dei test, Dockerfile, lockfile),
  stessi controlli (HE-REC-012). Un tag non è una messa in esercizio: la Release è «candidate» e la
  firma di HE-TPL-006 resta un atto umano (HE-SOP-004 par. 4).
- **GHCR, senza secret.** `ghcr.io/h-ealth/<repo>/<componente>`, login con il `GITHUB_TOKEN`.
  L'unico secret dei prodotti è `LINEAR_API_KEY` (lettura).
- **Riferimenti immutabili.** I prodotti chiamano `shared-workflows` con il tag completo; le action di
  terze parti sono pinnate allo SHA; i pin interni citano lo stesso tag.

## Workflow

Tutti hanno `on: workflow_call`, tranne `check.yml`: non partono da soli, li chiama un prodotto con `uses:`.

| Workflow | Cosa fa | Flusso | Controlli |
|---|---|---|---|
| `discover.yml` | legge `product.yaml` e i `component.yaml`, verifica le convenzioni e gli `arc`, produce la matrix | CI, rilascio | - |
| `pr-checks.yml` | branch, Closes/Part of, definizione di fatto, codici dei test, FROM pinnati | CI (PR) | CHK-001, 005, 008, 019 |
| `lint.yml` | ruff + mypy (python), eslint + tsc (node) | CI | CHK-012 |
| `test.yml` | tests/unit + tests/integration, JUnit, copertura con soglia | CI | CHK-010, 011 |
| `scan.yml` | Trivy sul filesystem: vulnerabilità con fix, segreti, misconfig | CI | CHK-015, 016 |
| `build.yml` | immagine locale → contenuto, Trivy, SBOM → push su GHCR `sha-<short>` | CI (push) | CHK-009, 017, 018 |
| `verify.yml` | compose con le immagini per digest, dati sintetici, tests/system | CI (push) | CHK-002 (test di sistema) |
| `release.yml` | promote, test-evidence, soup-evidence, traceability, release | rilascio | CHK-001...006, 020, 021 |
| `draft-docs.yml` | segnaposto, non ancora implementato | dopo il rilascio | - |
| `check.yml` | CI di questo repository: actionlint, ruff, pin interni | - | HE-REC-002 |

## Action

In `actions/`, composite, chiamate dai workflow con il tag completo. Gli script sono Python 3.12 di sola
libreria standard, con una libreria comune in `actions/_lib/helib.py` che legge i formati di HE-SOP-003
senza interpretarli.

| Action | Usata da | Output |
|---|---|---|
| `discover` | `discover.yml` | `product`, `components` (JSON) |
| `pr-checks` | `pr-checks.yml` | esito del job |
| `test-evidence` | `release.yml` | `test-report.csv`, `coverage.csv` |
| `soup-evidence` | `release.yml` | `scan-report.csv`, `<PROD>-REC-001_Lista-SOUP.csv`, `soup-diff.csv` |
| `traceability` | `release.yml` | `<PROD>-REC-002_Matrice-tracciabilita.csv`, `UserNeed_*.md`, `Requisiti_*.md` |
| `release-notes` | `release.yml` | `pull-requests.csv`, corpo della Release |
| `draft-docs` | `draft-docs.yml` | segnaposto, nessun output |

## Stato dell'enforcement

Alcune regole sono oggi **convenzioni, non vincoli applicati da GitHub** (piano Free, repository dei
prodotti privati). Vedi H-93.

| Regola | Stato |
|---|---|
| `gate` obbligatorio per il merge su `dev` e `main` dei prodotti (CHK-005, 007, 008, 010-012, 015, 016, 019) | non applicato |
| review di `@H-EALTH/engineering` obbligatoria (CHK-007) | non applicata (solo `CODEOWNERS`) |
| tag di versione non spostabili né cancellabili (CHK-020, HE-SOP-004 par. 2.3) | non applicato (nessun ruleset) |
| tag di `shared-workflows` non spostabili né cancellabili | non applicato |
