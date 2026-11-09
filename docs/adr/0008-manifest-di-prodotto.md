# 0008 — Il prodotto si dichiara con un manifest `product.yaml`
Data: 2026-11-09 · Stato: proposto

## Contesto
Con ADR 0007 il componente si dichiara in `component.yaml`, ma il prodotto non si dichiara da nessuna
parte: il prefisso del tag coincide con il nome del repository, la copertura minima è fissata nel
workflow, il codice QMS del prodotto (`SO-ARC-001`, `SO-REC-001`) e il progetto Linear non sono noti alla
pipeline. Le stazioni nuove (pr-checks, traceability, soup-evidence) hanno bisogno di tutti e quattro.
Il `ci.yml` del prodotto ripeteva i job per genere (`verify-python`, `verify-node`) perché `uses:` non
accetta espressioni (H-99).

## Decisione
Un file `product.yaml` nella radice del repository dichiara `codice` (prefisso dei documenti QMS),
`tag` (prefisso del tag di versione), `copertura_minima` e `linear_progetto`. `component.yaml` aggiunge
`arc`, il codice del componente in `docs/architecture/<codice>-ARC-001.md`, copia nel repository della
tabella dei componenti di HE-TPL-018. `discover` legge entrambi, verifica che ogni `arc` esista e
restituisce una sola lista `components` con il genere dentro: lint e test ricevono `kind` come input
e scelgono i passi, così il `ci.yml` del prodotto ha un job per stazione, non uno per genere.

## Conseguenze
Facile: la pipeline conosce il prodotto come lo conosce il QMS, con gli stessi codici; aggiungere un
genere non tocca i `ci.yml` dei prodotti; il nome del repository e il prefisso del tag possono
differire. Difficile: la tabella dei componenti va tenuta allineata con l'originale su Drive, che resta
la registrazione; un errore in `product.yaml` ferma tutta la CI.
Se si cambia idea: le chiavi di `product.yaml` tornano input dei workflow; `discover` non cambia
contratto.
