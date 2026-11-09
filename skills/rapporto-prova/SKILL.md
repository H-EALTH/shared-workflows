---
name: rapporto-prova
description: Bozza del rapporto di prova manuale (HE-TPL-024) per le prove che non girano in pipeline
---

# Bozza di HE-TPL-024 dal bundle

Prepara il rapporto delle prove **manuali** di questa versione, da eseguire da una persona diversa
dall'autore del codice (HE-SOP-005 par. 3.2 punto 4). I test automatici non usano questo modello.

## Cosa compilare dai dati

1. **Identificazione (par. 1).** Prodotto e versione provata: nome, x.y.z, tag e i digest di
   `artifacts.txt`. Oggetto: «prove manuali della versione x.y.z». Chi ha eseguito, data, ambiente,
   strumenti: `[DA COMPILARE: chi esegue la prova]`.
2. **Casi di prova (par. 2).** Un caso per riga, nell'ordine, per ciascuna di queste prove previste da
   HE-SOP-002 fase 6 punto 2, quando il requisito che la giustifica esiste nell'export `Requisiti_*.md`:
   - collaudo su dati reali o pseudonimizzati, per i requisiti che parlano di dati in ingresso o di
     sistemi del cliente;
   - prestazioni, per i requisiti con un tempo o una soglia numerica;
   - prove di sicurezza manuali, per i requisiti di autenticazione, autorizzazione, cifratura,
     validazione degli ingressi, registrazione degli accessi, aggiornabilità (HE-SOP-012 par. 7);
   - prova manuale di accessibilità (HE-SOP-017 par. 6), per i requisiti di accessibilità;
   - installazione, per i requisiti di installazione e manutenzione.
   Per ogni riga: colonna Requisito con il codice `REQ-nnn`; Precondizioni e Passi proposti dal testo
   del requisito, in forma di passi numerati; Risultato atteso: la frase del requisito riformulata come
   esito osservabile; Risultato ottenuto ed Esito: `[DA COMPILARE: chi esegue la prova]`.
   Un requisito già coperto da un test automatico superato (`test-report.csv`, esito PASS, stesso
   codice) non richiede una prova manuale: non lo elencare, salvo nelle cinque categorie sopra.
   Se nessun requisito rientra nelle categorie, una sola riga con `[DA COMPILARE: responsabile tecnico]`.
3. **Anomalie rilevate (par. 3).** Tabella vuota con intestazione.
4. **Riepilogo (par. 4).** Conteggi `[DA COMPILARE: chi esegue la prova]`; «Requisiti coperti»: i codici
   delle righe del par. 2.
5. **Firma (par. 5).** Riga vuota.

## Regole

- I passi sono una proposta: li scrivi solo quando il testo del requisito li rende evidenti; altrimenti
  `[DA COMPILARE: responsabile tecnico]`.
- Il risultato atteso si scrive prima di eseguire: non lasciarlo vuoto.
