# 0004 — La verifica di sicurezza è una stazione della pipeline e blocca su CRITICAL
Data: 2026-09-17 · Stato: proposto

## Contesto
La pagina Sicurezza dell'Engineering hub chiede uno scanner di vulnerabilità nella CI che faccia
fallire la build su una vulnerabilità critica; `HE-SOP-012` par. 10 chiede prove di sicurezza
complete prima di un rilascio. I componenti sono di generi diversi (ADR 0001): uno scanner dentro
la verifica di un singolo linguaggio lascerebbe fuori firmware e modelli. Le vulnerabilità
sfruttate stanno per lo più nelle immagini base e nelle dipendenze, non nel codice del team.

## Decisione
`platform` espone una stazione `scan`, indipendente dal linguaggio, basata su Trivy.
Sui sorgenti del componente cerca vulnerabilità nelle dipendenze, segreti e misconfigurazioni,
su PR e su `main`; sull'immagine pubblicata, per digest, cerca vulnerabilità del sistema
operativo e dei pacchetti, solo su `main`. Fallisce su `CRITICAL` con fix disponibile; la lista
di severità è un input. I report JSON restano 90 giorni come artifact del run e sono la prova di
sicurezza del commit. I rischi accettati stanno in `<path>/.trivyignore`, un CVE per riga, con il
riferimento all'anomalia `HE-SOP-006`.

## Conseguenze
Facile: ogni genere di componente si scansiona con la stessa stazione e lo stesso report;
l'auditor trova la prova accanto al run che ha prodotto l'artefatto; un segreto committato ferma
la PR prima del merge e, su `main`, ferma la pubblicazione dell'immagine.
Difficile: su `main` l'immagine viene pubblicata con tag `sha-…` e scansionata subito dopo; se la
scansione fallisce il tag esiste comunque e `release` lo risolverebbe. Un CVE critico
nell'immagine base blocca `main` finché il fornitore non pubblica il fix o il Dockerfile non lo
applica (ADR 0005). Le severità sotto `CRITICAL` non bloccano: vanno lette nel report.
Se si cambia idea: la stazione si sostituisce o si toglie dai `ci.yml` dei prodotti; il
contratto (`path`, `image`, report come artifact) resta valido con un altro scanner.
