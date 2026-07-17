# Contribuindo Com O CUTED

Obrigado por considerar uma contribuicao.

## Antes De Comecar

- Leia `AGENTS.md`, `PROJECT.md` e `docs/README.md`.
- Procure uma Issue ou PR existente.
- Nao use videos, transcricoes ou projetos privados como fixture.
- Nao inclua chaves, `.env`, cookies, certificados ou logs crus.
- Confirme que a fonte de qualquer midia de teste permite esse uso.

## Ambiente

O projeto principal e validado no Windows com Python 3.12 e Node.js 24.

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile tools/cutted/scripts/cutted.py
cd prototypes/live-timeline
npm ci
npm run build:lib
```

Mudancas no pipeline de render devem incluir um smoke real com midia sintetica
ou autorizada. Nao commite o MP4 resultante.

## Pull Requests

- Mantenha o escopo pequeno e explique o comportamento alterado.
- Adicione testes proporcionais ao risco.
- Atualize specs, ADRs ou a matriz de regressao quando o contrato mudar.
- Nao reorganize `tools/cutted/` sem um plano de migracao aprovado.
- Preserve processamento e armazenamento local por padrao.

Ao contribuir, voce concorda que sua contribuicao sera licenciada sob
AGPL-3.0, a mesma licenca do projeto.

## Issues

Relatos de bug devem trazer versao, Windows, comportamento esperado, resultado
observado e um exemplo minimo. Nao publique dados privados. Para falhas de
seguranca, use o fluxo privado descrito em `SECURITY.md`.
