---
codice: HE-TPL-022
titolo: Descrizione tecnica per l'installazione e l'esercizio
versione: "0.1"
stato: bozza
autore: Lorenzo Megliola
proprietario: responsabile tecnico
data_emissione: null
riferimenti:
  - IEC 82304-1:2016, par. 7.3
  - Regolamento (UE) 2017/745 (MDR), Allegato I par. 17.4 (se dispositivo medico)
  - EN IEC 81001-5-1:2022, par. 5.8
  - HE-SOP-012, HE-SOP-015
aliases:
  - HE-TPL-022
---

# HE-TPL-022 - Descrizione tecnica per l'installazione e l'esercizio

> **Come si usa.** Si copia in `10_Prodotti/<prodotto>/06_Regolatorio/`, si rinomina `<PROD>-DTE-001_Descrizione-tecnica_v0.1.md`, si compila e si elimina questo riquadro. È rivolta all'IT dell'azienda sanitaria. Porta la versione e si aggiorna a ogni messa in esercizio che cambia requisiti, configurazione o procedure di esercizio. Esce dall'azienda: seconda firma (HE-SOP-001 par. 3). Non contiene credenziali né segreti.

---

## 1. Identificazione

| | |
|---|---|
| Prodotto e versione | [nome, x.y.z] |
| Fabbricante e contatto tecnico | [H-EALTH, email di assistenza, email di sicurezza] |
| Componenti consegnati | [immagini container con digest, pacchetti] |

## 2. Architettura di esercizio

Schema dei componenti installati, delle porte esposte e dei flussi di rete. Rimando a `<PROD>-ARC-001` per il dettaglio.

## 3. Requisiti minimi

| | Minimo | Consigliato |
|---|---|---|
| Server: CPU, RAM, disco, GPU | | |
| Sistema operativo e versione | | |
| Runtime (Docker, Kubernetes) e versione | | |
| Database e versione | | |
| Rete: porte in ingresso e in uscita, banda, latenza verso i sistemi collegati | | |
| Browser degli utilizzatori | | |
| Sistemi esterni richiesti (interfacce, versioni provate) | | |

## 4. Installazione

Passi numerati, prerequisiti, come verificare che l'installazione è riuscita (gli stessi criteri del verbale di installazione HE-TPL-023), cosa fare se un passo fallisce. Tempo stimato.

## 5. Configurazione

Parametri configurabili, valore predefinito, effetto, chi può cambiarli. Le impostazioni di sicurezza (TLS, scadenza sessioni, livello dei log) con il valore raccomandato.

## 6. Avvio, arresto, riavvio

Comandi o procedure. Ordine dei componenti. Come verificare lo stato.

## 7. Sicurezza

| Tema | Cosa fornisce il prodotto | Cosa deve fare l'IT del cliente |
|---|---|---|
| Autenticazione e ruoli | [...] | [...] |
| Cifratura in transito e a riposo | [...] | [...] |
| Registrazioni di accesso | [cosa viene registrato, dove, senza dati sanitari] | [conservazione, inoltro al SIEM] |
| Aggiornamenti di sicurezza | [per quanto tempo, come si ricevono] | [finestra di manutenzione] |
| Segnalazione vulnerabilità | [indirizzo, tempi di risposta] | |
| Elenco componenti (SBOM) | [dove si trova, formato] | |

## 8. Copie di sicurezza e ripristino

Cosa va salvato (database, configurazione, modelli), con quale frequenza suggerita, come si ripristina, come si prova il ripristino.

## 9. Aggiornamento e ritorno alla versione precedente

Procedura di aggiornamento, verifiche dopo l'aggiornamento, procedura di rollback, tempo di indisponibilità atteso.

## 10. Monitoraggio

Indicatori esposti (salute dei servizi, code, errori), dove leggerli, soglie di allarme suggerite.

## 11. Fine del servizio

Cosa succede a fine contratto: consegna dei dati al titolare (formato, tempi), cancellazione delle copie, spegnimento e rimozione dei componenti, registrazione dell'avvenuta dismissione.

## 12. Limiti e problemi noti

Anomalie residue rilevanti per l'esercizio, dal documento di messa in esercizio.
