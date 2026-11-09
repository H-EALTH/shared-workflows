# Template QMS usati da draft-docs

Copie dei modelli del sistema di gestione che `draft-docs` compila in bozza. L'originale controllato
è su Drive (`H-EALTH_AZIENDA`, registro HE-REC-001): in caso di discordanza vale Drive.

| File | Modello | Bozza prodotta |
|---|---|---|
| `templates/HE-TPL-006_*.md` | documento di messa in esercizio | `MessaInEsercizio_<prodotto>_<x.y.z>.md` |
| `templates/HE-TPL-024_*.md` | rapporto di prova manuale | `Prova_manuale_<x.y.z>_<data>.md` |
| `templates/HE-TPL-021_*.md` | istruzioni per l'uso | `Proposta_<PROD>-IFU-001_<x.y.z>.md`, solo se una misura RC- è toccata |
| `templates/HE-TPL-022_*.md` | descrizione tecnica | `Proposta_<PROD>-DTE-001_<x.y.z>.md`, solo se il diff tocca `infra/` |

Il nome del file porta la versione del modello: quando il responsabile del sistema di gestione emette
una versione nuova, si aggiunge qui con una PR (il file con la versione più alta vince) e si pubblica un
tag `minor` di shared-workflows. Le istruzioni per la compilazione sono in `skills/<nome>/SKILL.md`.
