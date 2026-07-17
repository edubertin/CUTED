# Privacidade Do CUTED

Ultima atualizacao: 17 de julho de 2026.

## Resumo

CUTED e local-first. Ele nao cria uma conta CUTED, nao envia telemetria e nao
mantem um banco de dados hospedado de projetos.

## Dados No Computador

O aplicativo pode armazenar:

- videos importados ou copias temporarias;
- previews, frames, waveforms e analise de camera;
- transcricoes e legendas;
- estado de edicao e fila de render;
- renders finais;
- configuracoes, estimativas de uso e logs locais.

Projetos ficam normalmente em `Documents/CUTED Workspace`, renders em
`Videos/CUTED Renders` e configuracoes em `%USERPROFILE%\.cuted`.

## OpenAI Opcional

Recursos de transcricao, selecao, traducao ou direcao por IA podem enviar audio,
texto, contexto e metadados necessarios para a API OpenAI usando a chave do
usuario. O CUTED nao recebe essa chave em um servidor proprio.

A chave e salva localmente em `%USERPROFILE%\.cuted\.env.cuted.local`, nao em
HTML, localStorage, renders ou diagnosticos.

O tratamento realizado pela OpenAI segue os termos e politicas da conta usada
pelo usuario.

## YouTube

Ao importar um link autorizado, o CUTED usa `yt-dlp` e pode acessar o YouTube
para obter midia e legendas. O usuario e responsavel pelos direitos e termos
aplicaveis ao conteudo.

## Diagnosticos

`cuted.exe diagnostics` informa versao, sistema, disponibilidade de ferramentas
e indicadores booleanos de configuracao. Ele nao inclui chaves, videos,
transcricoes completas, cookies ou payloads crus de provedores.

Revise qualquer arquivo antes de compartilha-lo.

## Exclusao

O usuario controla os arquivos locais e pode remove-los pelo sistema. A
desinstalacao preserva workspace, renders e configuracoes por padrao para evitar
perda acidental. Esses dados podem ser apagados manualmente depois.

## Rede Local

A interface usa um servidor em `127.0.0.1`. Operacoes mutaveis exigem a sessao
local criada pelo CUTED. O servidor nao deve ser exposto em `0.0.0.0` ou em uma
interface de rede.
