# 0003 — I prodotti pinnano `platform` al tag completo; `platform` pinna le action terze allo SHA
Data: 2026-09-11 · Stato: proposto

## Contesto
I prodotti eseguono i workflow di `platform` tramite `uses:` con un
riferimento a una versione. Un riferimento mobile (`@v1`, `@main`) domani
punta a codice diverso: il run di ieri non è più riproducibile e non è
evidenza di quale logica di CI sia stata eseguita.
Lo stesso vale, dentro `platform`, per le action di terze parti: un tag
può essere spostato dal suo autore su un commit diverso.

## Decisione
Ogni cambiamento a `platform` passa da PR e produce un tag immutabile
`vX.Y.Z` con Release GitHub; il ruleset sui tag impedisce di spostarli.
I prodotti usano `H-EALTH/platform/...@vX.Y.Z`, mai `@v1` né `@main`.
Dentro `platform` le action di terze parti si pinnano allo SHA del commit,
con il tag corrispondente in commento; quelle GitHub-owned (`actions/*`)
al tag maggiore.
Dependabot (`github-actions`) apre la PR di aggiornamento nei prodotti:
il merge di quella PR è la traccia di quando il prodotto ha adottato la
nuova versione di piattaforma.

## Conseguenze
Facile: dal run CI si risale esattamente alla logica eseguita; il documento
di rilascio cita una versione precisa di piattaforma; il tag resta leggibile
e Dependabot sa proporre l'aggiornamento, cosa che con uno SHA non farebbe.
Difficile: ogni fix di piattaforma richiede una PR di adozione per prodotto
(Dependabot la apre, un umano la mergia); aggiornare una action terza in
`platform` richiede di cercarne lo SHA, non basta cambiare un numero.
Se si cambia idea: sostituire i tag nei `ci.yml` dei prodotti; nessun
cambiamento in `platform`.
