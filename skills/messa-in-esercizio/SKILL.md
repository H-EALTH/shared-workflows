---
name: messa-in-esercizio
description: Bozza del documento di messa in esercizio (HE-TPL-006) dal bundle della Release candidata
---

# Bozza di HE-TPL-006 dal bundle

Compila il modello HE-TPL-006 con i dati del bundle. Il risultato è una **bozza** per il responsabile
tecnico e regolatorio: la pipeline conosce i fatti (tag, commit, digest, test, matrice, SOUP, scansioni,
pull request), non le decisioni (esiti sì/no, valutazioni, riesame R3, firme).

## Cosa compilare dai dati

1. **Identificazione (par. 1).** Prodotto, versione x.y.z, tag, commit (SHA completo dal file
   `pull-requests.csv` o dai dati della versione), data di oggi. Tipo di messa in esercizio, redatto da,
   autorizzato da: `[DA COMPILARE: responsabile tecnico e regolatorio]`.
2. **Contenuto della versione (par. 2).** Una riga per ogni requisito presente nella matrice
   `<PROD>-REC-002_Matrice-tracciabilita.csv` con almeno una pull request in `pull-requests.csv`
   (colonna `pull_request` della matrice, colonna `numero` dell'elenco). Una riga per ogni issue citata
   dalla colonna `issue` di quelle righe. Il testo del requisito viene dall'export `Requisiti_*.md`.
3. **Condizioni verificate (par. 3).** Per ogni riga scrivi nella colonna Evidenza il file del bundle
   che la sostiene (`test-report.csv`, `coverage.csv`, matrice, `scan-report.csv`); la colonna Esito
   resta `[DA COMPILARE: responsabile tecnico e regolatorio]`, tranne quando i dati la decidono da soli:
   riga 1 e 2 sono «sì» solo se `test-report.csv` non ha esiti FAIL o ERROR e la matrice non ha righe
   con `note` = «requisito senza test»; in quel caso scrivi «sì (dalla pipeline)».
4. **Riesame R3 (par. 4).** Tutto `[DA COMPILARE: partecipanti al riesame R3]`: data, partecipanti,
   risposte, esito, azioni. Non inventare risposte.
5. **Anomalie residue (par. 5).** `[DA COMPILARE: product manager]`. Non scrivere «nessuna».
6. **Componenti di terzi (par. 6).** Dal file `soup-diff.csv`: una riga per variazione (componente,
   da versione, a versione); la colonna Valutazione cita le pull request di `pull-requests.csv` il cui
   titolo contiene il nome del componente, altrimenti `[DA COMPILARE: responsabile tecnico]`.
   Versione della lista SOUP di riferimento: `<PROD>-REC-001_Lista-SOUP.csv` generata al tag.
7. **Prove di sicurezza (par. 7).** Riga «Scansione»: conteggio per severità da `scan-report.csv`
   (vulnerabilità, segreti, misconfig) e la parola «nessuna critica» solo se non ci sono righe con
   severity CRITICAL. Riga «Test dei requisiti di sicurezza»: elenca i test di `test-report.csv` il cui
   codice REQ- corrisponde a requisiti di sicurezza nell'export Requisiti (autenticazione,
   autorizzazione, cifratura, validazione degli ingressi, registrazione degli accessi, aggiornabilità),
   altrimenti `[DA COMPILARE: responsabile tecnico]`. Prova di penetrazione e vulnerabilità residue:
   `[DA COMPILARE: responsabile della sicurezza delle informazioni]`.
8. **Informazioni di accompagnamento (par. 8).** `[DA COMPILARE: product manager]`.
9. **Come è stato prodotto l'artefatto (par. 9).** Pipeline: il workflow `release` del repository, con
   il link alla Release del tag. Artefatto prodotto: ogni riga di `artifacts.txt` (ref@digest). Dove è
   archiviato: `ghcr.io`, stessi ref. Ambiente di build: `[DA COMPILARE: responsabile tecnico]`.
10. **Par. 10 e 11.** `[DA COMPILARE: responsabile tecnico e regolatorio]`.
11. **Allegati (par. 12).** I file del bundle con il loro nome esatto, raggruppati come nell'elenco del
    modello.
12. **Firme (par. 13).** Righe vuote come nel modello.

## Regole

- Nessun numero o nome che non sia nei file: in dubbio, `[DA COMPILARE: ruolo]`.
- Mantieni le tabelle del modello; non aggiungere paragrafi.
- Il front-matter porta anche `tag: <tag>` e `commit: <sha>`.
