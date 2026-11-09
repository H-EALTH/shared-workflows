# 0002 — GHCR è il registry degli artefatti
Data: 2026-09-11 · Stato: proposto

## Contesto
L'ADR 0001 richiede un registry OCI in cui ogni componente deposita il
proprio artefatto e ne ottiene il digest. Serve per immagini container,
pesi di modelli e binari firmware allo stesso modo.
Le alternative (Docker Hub, registry cloud, Harbor self-hosted) aggiungono
un login, un sistema di permessi e un costo separati da GitHub, dove già
vivono codice, CI e Release.

## Decisione
Gli artefatti vanno su `ghcr.io/h-ealth/<prodotto>/<componente>`.
Un artefatto per componente. Login con il `GITHUB_TOKEN` del run e permesso
`packages: write`: nessun secret dedicato. I permessi di lettura del pacchetto
seguono quelli del repo del prodotto.
Le immagini container si pubblicano con Docker; ogni altro genere con `oras`.
Ogni push su `main` produce il tag `sha-<short>`; il tag di rilascio
`<prodotto>-vX.Y.Z` si aggiunge quando esiste. L'identificativo nel
documento di rilascio resta il digest, mai il tag.

## Conseguenze
Facile: stessi permessi del repo, nessuna credenziale da ruotare, un solo
dominio da seguire per l'auditor, nessuna fattura separata; formato OCI
standard, quindi copiabile verso qualunque altro registry con un comando.
Difficile: il server del cliente deve raggiungere `ghcr.io` in uscita con un
token in sola lettura. Se la rete è chiusa serve uno specchio interno: va
verificato prima del primo deploy, non scoperto durante.
Artefatti molto grandi (decine di GB) non sono il caso d'uso di GHCR; se un
modello li raggiunge, serve un ADR dedicato.
Se si cambia idea: cambia l'input `ref` di `publish` e `image` di
`build-image` nei prodotti, più il login; il resto della pipeline e la
struttura dei prodotti non se ne accorgono.
