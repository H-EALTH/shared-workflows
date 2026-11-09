# 0009 — L'immagine si pubblica solo dopo i controlli e il tag di versione si promuove senza ricostruire
Data: 2026-11-09 · Stato: proposto

## Contesto
In platform v0.4.0 `build-image` pubblicava l'immagine `sha-<short>` e `scan` la controllava dopo: un
commit con scan rosso aveva comunque un'immagine nel registry (ADR 0004, conseguenza difficile). Il QMS
chiede che nell'artefatto non entrino `experiments/` e `notebooks/` (CHK-009), che una vulnerabilità
critica blocchi la build (CHK-017) e che la SBOM nasca a ogni build (CHK-018). Il rilascio richiede un
artefatto prodotto solo dalla pipeline, con tag immutabile (CHK-020), senza ricostruire.

## Decisione
`build` costruisce l'immagine in locale (`load`), la controlla (contenuto, Trivy, SBOM) e solo poi la
pubblica come `sha-<short>`: un'immagine che non passa non esiste nel registry. Il digest assegnato dal
registry entra in `artifacts-<comp>`, che `e2e` fonde in `artifacts.txt`. `promote` ritrova
`artifacts.txt` nel run `ci` verde di `main` per il commit taggato e aggiunge il tag di versione agli
stessi digest con `imagetools create`, verificando che il digest non cambi.

## Conseguenze
Facile: ciò che è nel registry è passato dai controlli; la Release cita i digest già provati da `e2e`;
nessun secret oltre al `GITHUB_TOKEN`. Difficile: il build è a singola piattaforma (amd64), perché
`load` non accetta immagini multi-piattaforma; la scansione dell'immagine avviene prima del push, quindi
una vulnerabilità scoperta dopo si vede solo al build successivo o dai controlli periodici di
HE-SOP-012 par. 9.
Se si cambia idea: `build` torna a `push: true` e `scan` riprende l'input `image`; `promote` non cambia.
