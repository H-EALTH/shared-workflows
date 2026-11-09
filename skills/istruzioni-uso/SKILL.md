---
name: istruzioni-uso
description: Proposta di aggiornamento delle istruzioni per l'uso (HE-TPL-021) quando una misura RC- è toccata
---

# Proposta di aggiornamento di <PROD>-IFU-001

Una o più misure di controllo del rischio `RC-` sono attuate da requisiti toccati dalle pull request di
questa versione (colonne `rc` e `pull_request` della matrice). Le misure di tipo **informazione per la
sicurezza** vanno nel par. 5 delle istruzioni per l'uso (HE-SOP-007 par. 3 punto 5, HE-TPL-021). La
pipeline non sa di che tipo sia ciascuna misura: produci una **proposta** per il product manager.

## Cosa compilare dai dati

1. **Identificazione (par. 1).** Nome del prodotto, versione x.y.z, data. Fabbricante:
   `[DA COMPILARE: product manager]`.
2. **Par. 2-4, 6-10.** Una sola riga ciascuno: `[DA VERIFICARE: product manager] invariato salvo
   decisione diversa`.
3. **Avvertenze e limiti (par. 5).** Una riga per ogni misura `RC-` nell'elenco «Misure di controllo
   del rischio toccate da questa versione»: colonna Avvertenza con il testo del requisito che la attua
   (export `Requisiti_*.md`, riga con quel codice nella colonna RC) riformulato per l'utilizzatore;
   colonne Quando e Cosa fare `[DA COMPILARE: product manager]`; il codice in un commento nascosto
   `<!-- RC-nnn -->` subito dopo la riga. Se la misura non è di tipo informazione, il product manager
   cancellerà la riga: scrivilo in una nota sotto la tabella.

## Regole

- Frasi corte, un'azione per frase, nessun termine tecnico non spiegato.
- Il front-matter porta `proposta_per: <PROD>-IFU-001` e `rc: <elenco dei codici>`.
