Closes H-___

<!--
Collega la PR alla sotto-issue Linear (HE-SOP-003 par. 4 punto 8). `Closes H-n` se la PR completa la issue,
`Part of H-n` se ne fa solo una parte. Funziona solo qui, nella descrizione. Nessun codice REQ- nella PR:
li eredita dalla sotto-issue. Le PR di Dependabot: `Part of H-n` della issue Modifica di livello D della
prossima messa in esercizio (HE-SOP-004 par. 3.2) e la sezione «Aggiornamento di dipendenza» compilata.
-->

## Definizione di fatto (HE-SOP-003 par. 4.1)

Ogni casella spuntata, oppure `[ ]` seguita da `N/A: motivo`. `pr-checks` blocca `ci-ok` finché non è così.

- [ ] revisione di una persona diversa dall'autore
- [ ] test con il codice del requisito (`test_req_nnn`) o del componente (`test_arc_nnn`) superati in pipeline
- [ ] controlli automatici della pipeline superati (lint, test con copertura, scan)
- [ ] documentazione toccata aggiornata: architettura `docs/architecture/<PROD>-ARC-001.md`, istruzioni per l'uso, lista SOUP `docs/<PROD>-REC-001_Lista-SOUP.csv`
- [ ] anomalie aperte registrate come issue `Tipo: Anomalia` (HE-SOP-006)
- [ ] sicurezza (HE-SOP-012 par. 8): ingressi validati contro uno schema, query parametrizzate, nessun segreto nel codice

## Aggiornamento di dipendenza (solo se la PR aggiorna un componente di terzi, HE-SOP-004 par. 3.2)

| Riga | Contenuto |
|---|---|
| Cosa cambia | [patch / minore / maggiore; voci rilevanti del changelog] |
| Chi lo usa | [ARC-nnn] |
| Ruolo nella sicurezza | [sì / no, dalla lista SOUP] |
| Impatto | [nessuno / descrizione] |
