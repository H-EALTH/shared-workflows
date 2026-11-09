# SO-ARC-001 - Architettura del software

Copia nel repository del documento di architettura `<PROD>-ARC-001` (HE-TPL-018): `discover` e
`pr-checks` leggono la tabella dei componenti qui sotto per verificare i codici `arc` dei component.yaml
e i nomi `test_arc_nnn_...`. Lo schema grafico sta nella stessa cartella. L'originale controllato, con
versione e riesame R2, è su Drive in `02_Progettazione`.

## 2. Componenti

| ARC- | Nome | Cosa fa | Classe | Linguaggio e tecnologia | Repository e cartella | Requisiti attuati (codici) |
|---|---|---|---|---|---|---|
| ARC-001 | frontend | interfaccia web | A | TypeScript, React | app/frontend | |
| ARC-002 | backend | API | B | Python, FastAPI | app/backend | |

## 3. Interfacce

| Da | A | Tipo | Protocollo e formato | Dati scambiati | Chi è l'autorità sul dato |
|---|---|---|---|---|---|
| ARC-001 | ARC-002 | interna | HTTPS, JSON | | ARC-002 |
