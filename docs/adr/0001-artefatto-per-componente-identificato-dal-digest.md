# 0001 — Ogni componente produce un artefatto identificato dal digest
Data: 2026-09-11 · Stato: proposto

## Contesto
H-EALTH realizza prodotti di varia natura. Ogni prodotto è però una composizione di pochi
generi di componente: codice servito come container, applicazione web,
modello addestrato, binario firmware, libreria condivisa ecc.
La normativa di settore chiede che un rilascio sia riproducibile e che
si possa dimostrare quale esatto contenuto è finito in produzione.
Un'etichetta (tag, nome di versione) non basta: si può spostare.

## Decisione
La piattaforma standardizza i **generi di componente**, non i tipi di prodotto.
Ogni componente, qualunque sia il genere, produce un artefatto immutabile
pubblicato su un registry OCI e identificato dal suo digest sha256.
Il digest è l'unico identificativo che entra nel documento di rilascio.
Un prodotto è la lista dei digest dei suoi componenti a un dato tag.

## Conseguenze
Facile: un solo registry, un solo login, un solo tipo di identificativo
per l'auditor; aggiungere un genere nuovo non tocca i generi esistenti;
il deploy è sempre "tira questo digest", che sia un server o un dispositivo.
Difficile: anche pesi di modelli e binari firmware vanno impacchettati
come artefatti OCI, cosa meno comune di un'immagine container; chi rilascia
deve trascrivere digest lunghi, non nomi leggibili.
Se si cambia idea: il registry o il formato di pacchetto si sostituiscono
senza toccare la struttura dei prodotti, perché questi conoscono solo
"genere + digest".
