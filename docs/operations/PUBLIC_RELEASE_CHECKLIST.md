# Public Release Checklist

## Repository

- [ ] `main` contem a versao aprovada e CI verde.
- [ ] Gitleaks passou em todo o historico e todas as refs.
- [ ] Nao ha midia, transcricoes, `.env`, modelos ou builds rastreados.
- [ ] PRs, comentarios e logs de Actions foram revisados.
- [ ] Branches remotas obsoletas foram removidas.
- [ ] Descricao, topicos e imagem social estao atualizados.
- [ ] Ruleset de `main`, CodeQL, Dependabot e secret scanning estao ativos.

## Product Security

- [ ] Servidor vinculado a `127.0.0.1`.
- [ ] Operacoes mutaveis exigem cookie de sessao local.
- [ ] `Host` e `Origin` de operacoes mutaveis aceitam apenas loopback.
- [ ] Diagnosticos nao contem chave, video, transcricao ou payload cru.
- [ ] Importacao e abertura de caminhos permanecem limitadas ao fluxo local.

## Licensing

- [ ] `LICENSE` AGPL-3.0 presente e detectada pelo GitHub.
- [ ] `THIRD_PARTY_NOTICES.md` revisado.
- [ ] Licencas Python coletadas no artefato.
- [ ] Versao, hash, licenca e fonte correspondente do FFmpeg registrados.
- [ ] Assets de marca cobertos por `BRAND.md`.

## Installer

- [ ] Build portatil e smoke automatico passaram.
- [ ] Instalador compilou e checksum foi registrado.
- [ ] Teste em Windows limpo sem Python passou.
- [ ] Importacao, Smart Camera e render real passaram.
- [ ] Desinstalacao preservou workspace, configuracoes e renders.
- [ ] Decisao de assinatura digital registrada.

Nao publique o instalador enquanto os itens de Windows limpo, render real,
desinstalacao e assinatura permanecerem abertos. O repositorio de codigo pode
ser publico antes do binario.
