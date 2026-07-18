# Public Release Checklist

Status: first public beta published on 2026-07-17. Unchecked items remain
follow-up hardening work and must be reevaluated before a stable release.

## Repository

- [x] `main` contem a versao aprovada e CI verde.
- [x] Gitleaks passou em todo o historico e todas as refs.
- [x] Nao ha midia, transcricoes, `.env`, modelos ou builds rastreados.
- [x] PRs, comentarios e logs de Actions foram revisados.
- [ ] Branches remotas obsoletas foram removidas.
- [ ] Descricao, topicos e imagem social estao atualizados.
- [ ] Ruleset de `main`, CodeQL, Dependabot e secret scanning estao ativos.

## Product Security

- [x] Servidor vinculado a `127.0.0.1`.
- [x] Operacoes mutaveis exigem cookie de sessao local.
- [x] `Host` e `Origin` de operacoes mutaveis aceitam apenas loopback.
- [x] Diagnosticos nao contem chave, video, transcricao ou payload cru.
- [x] Importacao e abertura de caminhos permanecem limitadas ao fluxo local.

## Licensing

- [x] `LICENSE` AGPL-3.0 presente e detectada pelo GitHub.
- [x] `THIRD_PARTY_NOTICES.md` revisado.
- [x] Licencas Python coletadas no artefato.
- [ ] Versao, hash, licenca e fonte correspondente do FFmpeg registrados.
- [x] Assets de marca cobertos por `BRAND.md`.

## Installer

- [x] Build portatil e smoke automatico passaram.
- [x] Instalador compilou e checksum foi registrado.
- [ ] Teste em Windows limpo sem Python passou.
- [ ] Importacao, Smart Camera e render real passaram.
- [ ] Desinstalacao preservou workspace, configuracoes e renders.
- [x] Decisao de assinatura digital registrada: primeira beta unsigned, com aviso de SmartScreen.

A primeira beta foi publicada por autorizacao explicita do proprietario apos o
teste fisico do instalador. Os itens manuais ainda abertos nao invalidam essa
decisao historica, mas devem ser tratados como gates antes de uma release
estavel ou de uma nova distribuicao com garantias ampliadas.
