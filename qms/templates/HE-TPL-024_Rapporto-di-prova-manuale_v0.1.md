---
codice: HE-TPL-024
titolo: Rapporto di prova manuale
versione: "0.1"
stato: bozza
autore: Lorenzo Megliola
proprietario: responsabile tecnico
data_emissione: null
riferimenti:
  - IEC 62304:2006 + AMD1:2015, par. 5.6.7, 5.7.5, 9.8
  - HE-SOP-005 par. 3
aliases:
  - HE-TPL-024
---

# HE-TPL-024 - Rapporto di prova manuale

> **Come si usa.** Per le prove che non girano in pipeline: collaudo su dati reali, prove esplorative, prove di usabilità, prove di sicurezza manuali, riesecuzione dopo una correzione. Si copia in `10_Prodotti/<prodotto>/04_Verifica_Validazione/`, si rinomina `Prova_<oggetto>_<versione>_<AAAA-MM-GG>.md`, si compila durante la prova e si elimina questo riquadro. Le prove automatiche non usano questo modello: il loro rapporto è quello della pipeline.

---

## 1. Identificazione

| | |
|---|---|
| Prodotto e versione provata | [nome, x.y.z, tag, digest] |
| Oggetto della prova | [collaudo su dati reali / prova di sicurezza / riesecuzione dopo correzione H-n / ...] |
| Chi ha eseguito | [nome, ruolo]. Diverso dall'autore del codice provato |
| Data | [...] |
| Ambiente | [server, sistema operativo, browser, dati usati, sistemi collegati attivi o simulati] |
| Strumenti | [nome e versione di ogni strumento usato] |

## 2. Casi di prova

Un caso per riga. Il criterio di esito è scritto **prima** di eseguire.

| # | Requisito (codice) | Precondizioni | Passi | Risultato atteso | Risultato ottenuto | Esito |
|---|---|---|---|---|---|---|
| 1 | [REQ-nnn] | [...] | [1. ... 2. ...] | [...] | [...] | [superato / fallito / non eseguibile] |

## 3. Anomalie rilevate

| Caso | Descrizione | Gravità | Issue Linear |
|---|---|---|---|

## 4. Riepilogo

| | |
|---|---|
| Casi eseguiti | [n] |
| Superati | [n] |
| Falliti | [n] |
| Non eseguibili (con motivo) | [n] |
| Requisiti coperti | [elenco codici] |
| Conclusione | [la versione provata soddisfa i requisiti elencati / non li soddisfa per i casi N] |

## 5. Firma

| Nome | Ruolo | Data | Firma |
|---|---|---|---|
