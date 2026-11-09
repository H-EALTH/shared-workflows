---
name: descrizione-tecnica
description: Proposta di aggiornamento della descrizione tecnica (HE-TPL-022) quando il diff tocca infra/
---

# Proposta di aggiornamento di <PROD>-DTE-001

Il diff dal tag precedente tocca `infra/`: la descrizione tecnica per l'IT del cliente potrebbe dover
cambiare (HE-SOP-004 par. 4.2 condizione 7). Non riscrivere il documento: produci una **proposta**
sul modello HE-TPL-022 che dica, paragrafo per paragrafo, cosa va aggiornato e con quali dati.

## Cosa compilare dai dati

1. **Identificazione (par. 1).** Prodotto e versione; componenti consegnati: ogni riga di
   `artifacts.txt` (ref@digest). Fabbricante e contatti: `[DA COMPILARE: responsabile tecnico]`.
2. **Par. 2-11.** Per ciascuno scrivi una sola riga: `[DA VERIFICARE: responsabile tecnico] il diff
   tocca infra/: controllare se cambiano <argomento del paragrafo>`. Dove il bundle ha dati utili li
   citi: la SBOM (`sbom-<comp>.spdx.json`) per il par. 7 riga «Elenco componenti (SBOM)»; `soup-diff.csv`
   per i componenti di terzi aggiornati (par. 9, aggiornamento).
3. **Limiti e problemi noti (par. 12).** `[DA COMPILARE: dalle anomalie residue del documento di messa
   in esercizio]`.

## Regole

- Nessun comando, porta, percorso o parametro inventato: solo ciò che è nei file.
- Il front-matter porta `proposta_per: <PROD>-DTE-001`.
