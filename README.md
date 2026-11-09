# shared-workflows

Workflow GitHub Actions e action riutilizzabili per la CI/CD dei prodotti H-EALTH. Successore di
[`platform`](https://github.com/H-EALTH/platform) (`v0.4.0`): stesse decisioni (ADR 0001-0007), stesse
stazioni di base, in più le stazioni che il sistema di gestione richiede (HE-REC-012, controlli
CHK-001...021): regole sulla pull request, test con copertura, test di sistema, matrice di
tracciabilità, lista SOUP, registrazioni allegate alla Release, bozze dei documenti di messa in esercizio.

I prodotti pinnano il tag completo: `H-EALTH/shared-workflows/.github/workflows/<stazione>.yml@vX.Y.Z`.

## Indice

- [Repository `shared-workflows`](docs/README.md): principi, workflow, action, stato dell'enforcement.
- Un documento per flusso:
  - [CI del prodotto](docs/ci.md): `product.yaml`, `component.yaml`, i sette job più il gate, cosa
    fare quando una stazione fallisce;
  - [Rilascio del prodotto](docs/release.md): tag, versione candidata, le cinque stazioni, gli
    allegati di HE-TPL-006, le bozze di `draft-docs`;
  - [Rilascio di `shared-workflows`](docs/versionamento.md): tag, numerazione, pin interni.
- [Decisioni (ADR)](docs/adr/): il perché delle regole citate nei workflow.
- [Scaffold](scaffold/): i file da copiare in un repository prodotto.
- [Template QMS](qms/) e [skill](skills/) usati da `draft-docs`.
