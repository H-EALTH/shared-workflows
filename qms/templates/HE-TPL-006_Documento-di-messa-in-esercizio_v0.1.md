---
codice: HE-TPL-006
titolo: Documento di messa in esercizio
versione: "0.1"
stato: bozza
autore: Lorenzo Megliola
proprietario: responsabile tecnico e regolatorio
data_emissione: null
riferimenti:
  - IEC 62304:2006 + AMD1:2015, par. 5.8
  - UNI CEI EN ISO 13485:2021, par. 7.3.5, 7.3.8
  - HE-SOP-004 par. 4
  - HE-SOP-002 par. 4
aliases:
  - HE-TPL-006
---

# HE-TPL-006 - Documento di messa in esercizio

> **Come si usa.** Si copia in `10_Prodotti/<prodotto>/05_Messa_in_esercizio/`, si rinomina `MessaInEsercizio_<prodotto>_<x.y.z>.md`, si compila e si elimina questo riquadro. Un documento per ogni messa in esercizio, cioè per ogni versione autorizzata all'uso in esercizio (HE-SOP-004 par. 4.1): un tag senza messa in esercizio non richiede questo documento. Non si modifica dopo l'emissione.
>
> Il par. 4 è il verbale del riesame R3: si compila in riunione, con almeno due partecipanti, e sostituisce il verbale da HE-TPL-017 per R3. Per una messa in esercizio di livello D si compilano solo le righe del par. 3.
>
> L'autorizzazione alla messa in esercizio richiede la firma del **responsabile tecnico e regolatorio** (HE-SOP-001 par. 3). I ruoli sono associati a persone in HE-MAN-001 par. 5.

---

## 1. Identificazione

| | |
|---|---|
| Prodotto | [nome] |
| Versione messa in esercizio | [x.y.z] |
| Tag | [tag della versione] |
| Commit | [SHA completo] |
| Data | [data] |
| Tipo di messa in esercizio | [prima messa in esercizio / nuova funzione / correzione; livello A, B, C o D di HE-TPL-027 se è una modifica] |
| Redatto da | [nome] |
| **Messa in esercizio autorizzata da** | [responsabile tecnico e regolatorio: nome] |

## 2. Contenuto della versione

| Identificatore | Descrizione |
|---|---|
| [REQ-nnn] | [requisito implementato] |
| [issue FUNC H-n] | [funzione completata] |
| [issue Anomalia H-n] | [anomalia corretta] |
| [issue Modifica H-n] | [modifica attuata, livello] |

## 3. Condizioni di messa in esercizio verificate

Le otto condizioni di HE-SOP-004 par. 4.2.

| # | Condizione | Esito | Evidenza |
|---|---|---|---|
| 1 | Verifiche del piano complete e positive | [sì / no] | [rapporto dei test allegato; rapporti di prova manuale `Prova_...`] |
| 2 | Matrice di tracciabilità senza lacune | [sì / no] | [matrice allegata] |
| 3 | Riesame R3 svolto | [sì / no] | par. 4 |
| 4 | Rapporto di gestione del rischio firmato | [sì / no] | [codice, versione] |
| 5 | Anomalie e vulnerabilità residue valutate | [sì / no] | par. 5 e 7 |
| 6 | Prove di sicurezza complete (HE-SOP-012 par. 10) | [sì / no] | par. 7 |
| 7 | Istruzioni per l'uso e descrizione tecnica allineate alla versione | [sì / no] | par. 8 |
| 8 | Validazione completa, se richiesta per questa messa in esercizio (HE-SOP-005 par. 5 punto 4) | [sì / non richiesta: motivo] | [`Validazione_<versione>_<data>`, parte B] |

Se una riga è "no", non si mette in esercizio.

## 4. Riesame R3

| | |
|---|---|
| Data | [data] |
| Partecipanti e ruolo | [nome, ruolo; nome, ruolo]. Almeno due, di cui uno che non ha svolto il lavoro oggetto della messa in esercizio |

Si risponde con **sì**, **no** o **con riserva**. Un "no" o un "con riserva" genera un'azione.

| Domanda | Esito | Nota |
|---|---|---|
| Le otto condizioni del par. 3 sono tutte soddisfatte? | | |
| La matrice di tracciabilità è senza lacune? | | |
| Le anomalie residue sono elencate e valutate una per una? | | |
| Il rapporto di gestione del rischio è aggiornato e firmato? | | |
| La validazione richiesta è conclusa con esito "validato"? | | |
| Istruzioni per l'uso e descrizione tecnica sono aggiornate alla versione? | | |
| Il piano di sviluppo e il piano di manutenzione descrivono ancora il progetto reale? | | |

| Esito complessivo | [approvato / approvato con azioni / non approvato] |
|---|---|

| # | Azione | Bloccante? | Chi | Entro | Issue Linear |
|---|---|---|---|---|---|
| 1 | [cosa] | [sì / no] | [nome] | [data] | [H-n] |

Un'azione bloccante impedisce la messa in esercizio finché non è chiusa. Le firme dei partecipanti sono al par. 13.

## 5. Anomalie residue note

Elenco completo delle anomalie note e non corrette alla data della messa in esercizio. **Ognuna richiede una valutazione esplicita.**

| Issue | Descrizione | Impatto sull'utilizzatore | Contribuisce a un rischio non accettabile? | Motivazione | Quando si prevede di correggerla |
|---|---|---|---|---|---|
| [ID] | [cosa non funziona] | [cosa vede l'utente] | **no** | [perché no] | [versione] |

Se nessuna: scriverlo esplicitamente. Un elenco vuoto senza dichiarazione non è una registrazione.

## 6. Componenti di terzi

Versione della lista SOUP di riferimento: [`<PROD>-REC-001`, data, generata al tag]. Componenti cambiati rispetto alla messa in esercizio precedente:

| Componente | Da versione | A versione | Valutazione (HE-SOP-004 par. 3.2) |
|---|---|---|---|
| [nome] | [x] | [y] | [pull request #n; issue Modifica H-n se richiesta] |

## 7. Prove di sicurezza

| Prova | Esito | Evidenza |
|---|---|---|
| Scansione delle vulnerabilità su codice, dipendenze e immagini | [nessuna critica / elenco] | [esecuzione della pipeline] |
| Test dei requisiti di sicurezza | [superati] | [rapporto dei test] |
| Prova di penetrazione | [eseguita il, da / non richiesta: eseguita il ... prima della prima messa in esercizio, architettura ed esposizione in rete invariate] | [`Prova_sicurezza_<versione>_<data>`] |
| Vulnerabilità residue note | [elenco o "nessuna"] | dichiarazione: nessuna contribuisce a un rischio non accettabile |

## 8. Informazioni di accompagnamento

| Documento | Versione consegnata con questa messa in esercizio | Cambiata rispetto alla messa in esercizio precedente? |
|---|---|---|
| Istruzioni per l'uso `<PROD>-IFU-001` | [versione] | [sì / no] |
| Descrizione tecnica `<PROD>-DTE-001` | [versione] | [sì / no] |
| Video di formazione | [versione, se cambiati] | [sì / no] |

## 9. Come è stato prodotto l'artefatto

| | |
|---|---|
| Pipeline | [quale, con il link all'esecuzione] |
| Ambiente di build | [immagine, versioni] |
| Artefatto prodotto | [nome e digest dell'immagine, o pacchetto] |
| Dove è archiviato | [registry, percorso] |

L'artefatto deve essere riproducibile da queste informazioni.

## 10. Uso previsto di questa messa in esercizio

[Esercizio ordinario, oppure sperimentazione: in quel caso si dichiara che le proposte prodotte non sono usate per programmare davvero, e da quando lo saranno.]

## 11. Consegna e installazione

[Come l'artefatto è stato consegnato al cliente; verbale di installazione `Installazione_<cliente>_<versione>_<data>` quando compilato.]

## 12. Allegati

- rapporto dei test automatici della versione [x.y.z]
- matrice di tracciabilità esportata (`<PROD>-REC-002`)
- elenco delle pull request incluse, con gli approvatori
- distinta dei componenti software (SBOM)
- esito delle scansioni di sicurezza
- per i prodotti fisici: rapporti di prova e registrazione di realizzazione dell'esemplare consegnato

La prova dei test è la copia allegata, non il log della pipeline.

## 13. Firme

| Nome | Ruolo | Data | Firma |
|---|---|---|---|
| | responsabile tecnico e regolatorio (autorizzazione alla messa in esercizio) | | |
| | partecipante al riesame R3 | | |
| | partecipante al riesame R3 | | |
