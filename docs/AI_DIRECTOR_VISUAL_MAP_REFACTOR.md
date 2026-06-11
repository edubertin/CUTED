# AI Director Visual Map Refactor

## Objetivo

Transformar o fluxo de camera do CUTED em um sistema visual-map-first:

- o usuario aciona um unico botao **IA** no player;
- o app usa um mapa visual local para entender pessoas, lados, confianca e janelas de reacao;
- a IA atua como diretora editorial, nao como detectora primaria;
- a timeline de keyframes continua sendo o ponto de ajuste manual;
- o menu antigo de Smart Camera sai da experiencia principal.

## Decisao de Produto

O produto deve parecer simples: um botao de IA gera a direcao, e a timeline permite corrigir.
Controles avancados de camera nao devem competir com o fluxo principal.

## Decisao Tecnica

YOLO/person detection passa a ser a fonte principal de mapeamento de pessoas e contexto corporal.
OpenCV deixa de ser responsavel por decisao de camera e deteccao editorial.

Observacao: bibliotecas internas podem ainda usar mecanismos de leitura de video, mas a regra de negocio nao deve depender de OpenCV como motor de direcao.

## Arquitetura Alvo

1. Import cria previews rapidamente.
2. Um processo local cria ou atualiza `visual-map.json` em background.
3. O botao **IA** consome:
   - `visual-map.json`;
   - transcript/timestamps;
   - metadados do clip;
   - poucos frames apenas quando houver incerteza.
4. A IA retorna um `director_plan`.
5. O sistema local converte o plano em `camera_path`.
6. A timeline exibe e permite editar o resultado.

## Regras de Negocio

- A camera deve evitar ficar parada por mais de 10 a 15 segundos; alvo atual: 12 segundos.
- Em videos com duas pessoas, o diretor deve cobrir ambos os lados quando houver deteccao confiavel.
- `fit/blur` e plano aberto sao fallback seguro, nao substituto para foco quando existe pessoa confiavel.
- Labels da timeline precisam refletir o frame aplicado; a UI nao deve prometer "interlocutor" quando o frame real e apenas `fit=contain`.
- Frames enviados para IA devem ser excecao, usados para incerteza, expressao ou validacao pontual.
- O custo deve ser controlado: preferir dados estruturados locais a imagens na IA.

## Performance

YOLO nao deve travar o app:

- rodar em background;
- usar amostragem inteligente;
- reusar cache por arquivo/import;
- permitir mapa parcial;
- aumentar precisao apenas em trechos candidatos;
- registrar status claro quando o mapa ainda esta sendo preparado.

## Etapas

### Etapa 1 - Memoria e Contratos

- Criar este documento.
- Definir contrato minimo do visual map.
- Registrar criterios de teste.

### Etapa 2 - Visual Map First

- Priorizar `visual-map.json` na rota de camera.
- Criar fallback de mapa por clip quando o mapa global nao existir.
- Preferir YOLO/person para pessoas e lados.
- Remover OpenCV da decisao editorial principal.

### Etapa 3 - AI Director Sem Fotos Por Padrao

- Montar payload estruturado para IA com pessoas, lados, confianca, janelas e transcript.
- Reduzir envio de frame para modo de incerteza.
- Registrar diagnostico de custo/entrada.

### Etapa 4 - UI Simples

- Remover menu antigo de Smart Camera da experiencia principal.
- Criar botao **IA** no player.
- Manter timeline de camera abaixo do player.
- Garantir loading e status do botao.

### Etapa 5 - QA Com Caches Reais

- Validar no import atual sem novo import inicialmente.
- Usar `clip-001` para cobertura esquerda/direita.
- Usar `clip-004` para validar interlocutor e fallback de YOLO.
- Reimportar somente no final, se necessario.

### Etapa 6 - Documentacao e Git

- Atualizar docs de regra de negocio e arquitetura.
- Rodar testes.
- Commit e push quando a etapa estiver consistente.

## Criterios de Aceite

- Usuario ve apenas o botao **IA** como acao principal de camera.
- Timeline continua funcionando para edicao manual.
- `clip-004` nao deve gerar label de interlocutor com camera sem foco quando ha pessoa confiavel.
- `clip-001` deve manter cobertura dos dois lados.
- Testes automatizados passam.
- O app segue utilizavel enquanto o mapa visual roda em background.

## Status

- 2026-06-11: refactor iniciado; plano registrado.
- 2026-06-11: `visual-map-v2` adotado; YOLO/person virou fonte preferencial do mapa visual.
- 2026-06-11: botao unico **IA** adicionado ao player; painel Smart Camera removido da experiencia principal.
- 2026-06-11: AI Director passa a usar payload estruturado sem frames quando a cobertura visual local e suficiente.
