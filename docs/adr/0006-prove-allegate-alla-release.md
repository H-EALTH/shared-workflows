# 0006 — Le prove del commit rilasciato si allegano alla Release e il rilascio si ferma se mancano
Data: 2026-09-18 · Stato: proposto

## Contesto
`scan` e `verify-python` producono report Trivy e JUnit come artifact del run `ci`, che GitHub
cancella dopo 90 e 30 giorni. La SBOM nasce in `release` ed era l'unica prova allegata. Il
fascicolo tecnico deve conservare le prove di verifica e sicurezza per la vita del prodotto
(`HE-SOP-012` par. 10): un link a un artifact scaduto non è una prova. Inoltre `release`
verificava solo l'esistenza del tag `sha-<short>`, che `build-image` crea prima dello scan
dell'immagine (ADR 0004): un commit con scan rosso restava rilasciabile.

## Decisione
`release` recupera dal run `ci` concluso con successo per il commit taggato gli artifact
`scan-*` e `junit-*`, li converte insieme alla SBOM in tre cartelle, `security/`, `SBOM/`,
`tests/`, ciascun file in formato originale, tabella `.txt` e `.csv`, e le allega alla
Release come zip. Se il run `ci` verde non esiste, se i suoi artifact sono scaduti o se il
caricamento degli allegati fallisce, il rilascio si ferma: una Release senza prove non è valida.
Il chiamante dichiara `actions: read`.

## Conseguenze
Facile: la Release è il fascicolo completo del rilascio; auditor e documento di rilascio su
Drive trovano digest, SBOM, scanner e test in un solo posto e in un formato leggibile senza
strumenti; un commit il cui scan dell'immagine è fallito non si può più rilasciare.
Difficile: non si può taggare un commit più vecchio di 30 giorni senza un nuovo run `ci`; gli
asset di una Release sono piatti, quindi le cartelle viaggiano come zip; il prodotto deve
aggiungere a mano `actions: read`, che Dependabot non propone. La cartella `SBOM/` impone alla
cartella di lavoro di syft il nome `sbom-raw/`, perché su filesystem case-insensitive le due
collidono.
Se si cambia idea: le prove restano negli artifact del run `ci` come prima; si toglie il passo
di recupero da `release` e il permesso dai prodotti, il resto della stazione non cambia.
