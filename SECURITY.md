# Politica De Seguranca

## Versoes Suportadas

O CUTED esta em beta. Correcoes de seguranca sao aplicadas na branch `main` e na
release publica mais recente, quando houver.

## Como Reportar

Nao abra uma Issue publica para vulnerabilidades.

Use o recurso **Report a vulnerability** na aba Security do repositorio:

https://github.com/edubertin/CUTED/security/advisories/new

Inclua uma descricao curta, impacto, passos de reproducao e a versao afetada.
Nao envie chaves, videos, transcricoes completas, cookies, caminhos privados ou
dados pessoais. Um projeto sintetico e o arquivo gerado por
`cuted.exe diagnostics` sao preferiveis.

## Escopo Sensivel

Os pontos de maior impacto sao:

- operacoes da API local em `127.0.0.1`;
- selecao, abertura ou remocao de arquivos locais;
- importacao e renderizacao por subprocessos;
- armazenamento da chave OpenAI;
- parsing de videos, legendas, JSON e assets nao confiaveis;
- instalador, atualizacoes e cadeia de build.

O servidor local nao deve ser exposto na rede. Relate qualquer forma de acionar
operacoes mutaveis sem a sessao local do CUTED.

O servidor valida `Host` antes de servir paginas, arquivos ou APIs. Depois da
navegacao inicial, leituras e escritas exigem a sessao local; escritas tambem
validam `Origin`. Dados de projeto incorporados no HTML sao escapados para
contexto de script.

## Expectativa De Resposta

O recebimento sera confirmado quando possivel. A divulgacao publica deve esperar
uma correcao ou mitigacao coordenada. Este projeto nao oferece atualmente um
programa pago de bug bounty.
