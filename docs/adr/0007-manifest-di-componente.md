# 0007 — Un componente si dichiara con un manifest `component.yaml`
Data: 2026-10-01 · Stato: proposto

## Contesto
Con la scoperta automatica (H-134) un componente era una cartella in `components/*/` con un
`pyproject.toml`: la CI lo riconosceva dalla posizione e ne deduceva il genere. Così la piattaforma
imponeva la struttura delle cartelle e un solo linguaggio, mentre i prodotti H-EALTH hanno
architetture diverse (web, firmware, modelli). La logica di scoperta era inoltre copiata nel
`ci.yml` e nel `release.yml` di ogni prodotto.

## Decisione
Un componente è una cartella, a qualunque profondità tranne la radice, che contiene un
`component.yaml` con il suo genere (`kind`). Il workflow riusabile `discover` di `platform` trova i
manifest, ne verifica le convenzioni e restituisce i componenti per genere. Il nome del componente
è il nome della cartella, unico nel repo. Il prodotto dichiara in `kinds` i generi che gestisce: un
manifest di un altro genere fa fallire la CI.

## Conseguenze
Facile: la struttura delle cartelle è libera; il genere è esplicito e verificabile; la scoperta si
mantiene in un solo punto, versionato con ADR 0003; il contratto di ADR 0001 non cambia.
Difficile: `uses:` non accetta espressioni, quindi un genere nuovo richiede i suoi job nel
`ci.yml` del prodotto oltre alla stazione in `platform`; Dependabot non legge il manifest e copre
i componenti con un glob.
Se si cambia idea: lo smistamento per genere può passare in un `verify.yml` di `platform`
senza toccare i manifest dei prodotti.
