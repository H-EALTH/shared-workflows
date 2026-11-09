# 0005 — L'immagine base è pinnata al digest e riceve gli aggiornamenti di sicurezza a build time
Data: 2026-09-17 · Stato: proposto

## Contesto
Un tag di immagine base (`python:3.12-slim`) è mobile: il fornitore lo ricostruisce e due build a
giorni di distanza partono da contenuti diversi. È lo stesso problema dell'ADR 0003 per le action.
Al primo run di `scan` (ADR 0004) l'immagine `hello` conteneva tre CVE critici in `perl-base`
ereditati da Debian: il fix esisteva in Debian ma non era ancora nell'immagine `python`.
La pagina Sicurezza chiede dipendenze aggiornate e controllate da Dependabot.

## Decisione
Il `FROM` indica tag e digest: `python:3.12-slim@sha256:…`. Docker usa il digest; il tag serve a
Dependabot (`package-ecosystem: docker`) per proporre in PR il digest nuovo quando il fornitore
ricostruisce il tag. Subito dopo il `FROM` il Dockerfile applica gli aggiornamenti di sicurezza
della distribuzione (`apt-get update && apt-get upgrade -y`). L'identificativo del rilascio resta
il digest dell'immagine prodotta, non quello della base (ADR 0001).

## Conseguenze
Facile: la base cambia solo con una PR che passa da `scan`; un CVE del sistema operativo con fix
in Debian si chiude al build successivo, senza aspettare il fornitore dell'immagine.
Difficile: l'`apt-get upgrade` rende il build non riproducibile bit per bit dallo stesso digest
di base, perché prende i pacchetti disponibili in quel momento. La riproducibilità che conta è
quella dell'artefatto pubblicato, identificato dal digest e descritto dalla SBOM: è ciò che il
cliente riceve e che il documento di rilascio cita. Chi volesse la base identica a ogni build
toglie l'`upgrade` e aspetta il digest nuovo del fornitore, accettando finestre di esposizione
più lunghe.
Se si cambia idea: si tocca il solo Dockerfile del componente; `scan` e `release` non cambiano.
