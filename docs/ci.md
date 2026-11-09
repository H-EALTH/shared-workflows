# Flusso CI del prodotto

Parte su ogni pull request verso `dev` e `main` e su ogni push su `dev` e `main`, dal `ci.yml` del
prodotto ([scaffold](../scaffold/.github/workflows/ci.yml)). Sette job più il gate. Dopo `discover`,
`pr-checks`, `lint`, `test` e `scan` partono in parallelo; `build` ed `e2e` solo su push.

```mermaid
flowchart LR
    D[discover] --> P[pr-checks]
    D --> L["lint<br>× componente"]
    D --> T["test<br>× componente"]
    D --> S["scan<br>× componente"]
    L --> B["build<br>× componente, solo push"]
    T --> B
    S --> B
    B --> E["e2e<br>solo push"]
    P --> OK[ci-ok]
    E --> OK
```

## Manifest

### `product.yaml`, nella radice (ADR 0008)

```yaml
codice: SO                                   # prefisso dei documenti QMS: SO-ARC-001, SO-REC-001, SO-REC-002
tag: so-ulss2                                # prefisso del tag: so-ulss2-vX.Y.Z (HE-SOP-004 par. 2.1)
copertura_minima: 80                         # soglia di test.yml, in percento (HE-TPL-003 par. 4)
linear_progetto: "Sale Operatorie — Pilota ULSS2"   # progetto Linear con i documenti User Need e Requisiti
```

Quattro chiavi, tutte obbligatorie, nessun'altra. `linear_progetto` accetta il nome esatto, lo slug o
l'id del progetto.

### `component.yaml`, in ogni cartella componente (ADR 0007)

```yaml
kind: python     # python | node
arc: ARC-002     # codice del componente in docs/architecture/<codice>-ARC-001.md
```

- `kind` sceglie i passi di `lint` e `test` e i file obbligatori (tabella sotto).
- `arc` deve essere la prima cella di una riga della tabella dei componenti di
  `docs/architecture/<codice>-ARC-001.md`, copia nel repository della tabella di HE-TPL-018 par. 2
  (l'originale controllato resta su Drive). Lo stesso file serve a `pr-checks` e `traceability` per i
  nomi `test_arc_nnn_...`.
- Il nome del componente è il nome della cartella: minuscolo, unico, è anche il nome dell'immagine.

| `kind` | lint | test | File obbligatori |
|---|---|---|---|
| `python` | `ruff check`, `ruff format --check`, `mypy .` | `pytest tests/unit tests/integration` con `--cov-fail-under` | `Dockerfile`, `pyproject.toml`, `requirements-dev.txt` (ruff, mypy, pytest, pytest-cov) |
| `node` | `npm run lint`, `npm run typecheck` | `npm test -- tests/unit tests/integration` (vitest run, `@vitest/coverage-v8`) | `Dockerfile`, `package.json`, `package-lock.json` |

In `pyproject.toml` conviene `[tool.coverage.run] omit = ["tests/*"]`, altrimenti i test contano nella
copertura.

## Job

| Job | Stazione | Quando | Output | Controlli |
|---|---|---|---|---|
| `discover` | `discover.yml` | sempre | `components` (JSON: name, path, kind, arc), `product` (JSON) | ADR 0007, 0008 |
| `pr-checks` | `pr-checks.yml` | solo PR | esito | CHK-001, 005, 008, 019 |
| `lint (<nome>)` | `lint.yml` | sempre | artifact `lint-<nome>` (log, 30 giorni) | CHK-012 |
| `test (<nome>)` | `test.yml` | sempre | artifact `test-<nome>` con `junit.xml`, `coverage.xml` (90 giorni) | CHK-010, 011 |
| `scan (<nome>)` | `scan.yml` | sempre | artifact `scan-<nome>` (90 giorni) | CHK-015, 016 |
| `build (<nome>)` | `build.yml` | solo push | `ghcr.io/h-ealth/<repo>/<nome>:sha-<short>`; artifact `scan-<nome>-image`, `sbom-<nome>`, `artifacts-<nome>` | CHK-009, 017, 018 |
| `e2e` | `e2e.yml` | solo push, dopo build | artifact `e2e` (`junit.xml`), `artifacts` (`artifacts.txt`) | CHK-002 |
| `ci-ok` | nel `ci.yml` del prodotto | sempre | - | gate |

`ci-ok` ha un nome fisso ed è l'unico check da richiedere nella branch protection: i nomi dei job in
matrix cambiano con i componenti. È verde se tutti gli altri sono `success` o `skipped`.

## pr-checks

Un job senza matrix. Legge la PR con l'API GitHub e il documento Requisiti del progetto Linear
(secret `LINEAR_API_KEY`). Non blocca `build`, blocca solo `ci-ok`. Verifica:

| Controllo | Regola | Riferimento |
|---|---|---|
| branch | `<tipo>/h-<numero>-<descrizione>` in minuscolo; tipi `feat fix hotfix docs refactor chore experiment test`; i branch `dependabot/` sono esenti | HE-SOP-004 par. 2.1 |
| closes | la descrizione contiene `Closes H-n` o `Part of H-n` (o i sinonimi di `.github/CONTRIBUTING.md`) | HE-SOP-003 par. 4 punto 8, CHK-005 |
| definizione di fatto | ogni casella `[x]`, oppure `[ ]` con `N/A: motivo`; nessuna casella = modello non usato | HE-SOP-003 par. 4.1, CHK-008 |
| test | ogni `test_req_nnn` nei file toccati esiste nel documento Requisiti; ogni `test_arc_nnn` esiste in `<PROD>-ARC-001.md` | HE-SOP-003 par. 4 punto 9, CHK-001 |
| dockerfile | ogni `FROM` nei Dockerfile toccati è pinnato `@sha256:` (esclusi `scratch` e gli stage) | ADR 0005, CHK-019 |

La descrizione della PR si legge a ogni esecuzione: il `ci.yml` del prodotto ascolta anche `edited`,
così correggerla fa ripartire la CI. Le PR di Dependabot passano dagli stessi controlli: chi le fonde
compila la sezione «Aggiornamento di dipendenza» del modello e il `Part of H-n` della issue Modifica di
livello D (HE-SOP-004 par. 3.2).

## build ed e2e

`build` costruisce l'immagine in locale e la pubblica solo dopo tre controlli (ADR 0009): nessun file
di `experiments/` o `notebooks/` dentro (CHK-009, si rimedia con `.dockerignore`); Trivy sull'immagine,
che blocca su `CRITICAL` con fix (CHK-017); SBOM SPDX con syft (CHK-018). Il digest assegnato dal
registry finisce in `artifacts-<nome>`.

`e2e` fonde gli `artifacts-<nome>` in `artifacts.txt`, esporta `IMAGE_<NOME>` (nome in maiuscolo, `-` e
`.` → `_`), avvia `tests/system/compose.yaml` con `docker compose up --wait` (servono gli
`healthcheck`), esegue `tests/system/seed.sh` se esiste (dati sintetici, mai dati di paziente) e poi
`pytest tests/system`, i test di sistema con il codice del requisito nel nome
(`test_req_012_...`). Dipendenze in `tests/system/requirements.txt`.

## Quando una stazione fallisce

| Stazione | Causa | Cosa fare |
|---|---|---|
| `discover` | `product.yaml` assente o con chiavi sbagliate; `component.yaml` senza `kind` o `arc`; `arc` assente da `<PROD>-ARC-001.md`; nome duplicato; file obbligatorio mancante | il messaggio indica file e causa |
| `pr-checks` | vedi la tabella sopra | correggere branch, descrizione, nomi dei test o Dockerfile; la descrizione si può modificare senza nuovi commit |
| `lint` | ruff, mypy, eslint o tsc rosso | leggere `lint-<nome>` |
| `test` | test rosso, o copertura sotto `copertura_minima` | il riepilogo di pytest o vitest nel log |
| `scan` | `CRITICAL` con fix, un segreto, un errore nel Dockerfile | aggiornare la dipendenza; un segreto va **ruotato subito** (HE-SOP-012 par. 2); un rischio accettato va in `<path>/.trivyignore` con il riferimento all'anomalia HE-SOP-006 |
| `build` | cartella di esplorazione nell'immagine; `CRITICAL` nell'immagine base | `.dockerignore`; aggiornare il digest del `FROM` (ADR 0005) |
| `e2e` | servizio non pronto, test di sistema rosso, nessun test raccolto | i log dei servizi sono nel job; ogni requisito ha almeno un test in `tests/system` |

## Dependabot

Il `dependabot.yml` dello scaffold aggiorna il tag di `shared-workflows` (`github-actions`), le
immagini base (`docker`), `pip` e `npm` di ogni cartella sotto `app/`. Dependabot non legge i
`component.yaml`: un componente fuori da `app/` va aggiunto a mano.
