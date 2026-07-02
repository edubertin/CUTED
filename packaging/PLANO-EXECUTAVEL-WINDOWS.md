# Plano: CUTED como Executável Windows (Beta Local)

Status: proposto
Data: 2026-06-10
Relacionado: [SPEC-011 Local Beta Installer](../docs/product/SPEC-011-local-beta-installer.md),
[ADR-0001](../docs/architecture/ADR-0001-skill-to-app-migration.md),
[ADR-0003](../docs/architecture/ADR-0003-local-hybrid-vision-engine.md),
[SPEC-007](../docs/product/SPEC-007-openai-settings-and-cost-ledger.md)

Atualizacao 2026-07-02: o app foi reposicionado como distribuicao gratuita.
O caminho de instalador continua valido, mas a experiencia publica deve abrir
uma janela desktop real via pywebview/WebView2, com navegador externo apenas
como fallback de desenvolvimento/suporte. Roadmap: [PLAN-004](../docs/product/PLAN-004-windows-desktop-shell-and-free-distribution.md).

## 1. Objetivo

Entregar o CUTED como um programa Windows que uma pessoa leiga consegue
instalar com duplo clique, abrir pelo Menu Iniciar, importar um vídeo, editar
no navegador e encontrar os MP4 finais — sem Python, sem terminal, sem Codex.

Este plano aprofunda a SPEC-011 com decisões técnicas validadas por pesquisa.
A pasta `packaging/` é o lar de todo o trabalho de empacotamento: scripts de
build, spec do PyInstaller, script do instalador e licenças de terceiros. O
código do app (`tools/cutted/`) permanece a implementação de referência e não
deve ser reorganizado para isso funcionar.

## 2. Decisões Técnicas (com justificativa)

### 2.1 PyInstaller em modo `onedir` — nunca `onefile`

- `onefile` extrai tudo para uma pasta temporária a cada execução. Esse
  comportamento é o mesmo padrão de "packers" de malware e é gatilho conhecido
  de falsos positivos de antivírus, além de deixar o start lento em apps
  grandes.
- `onedir` gera uma pasta com `cuted.exe` + dependências ao lado. Sem extração
  em runtime, menos suspeito para AV e start mais rápido.
- A "feiura" da pasta é resolvida pelo instalador (seção 2.4): o usuário só vê
  o atalho.

### 2.2 Dependências em camadas — o pacote NÃO leva tudo

O `cutted.py` já foi projetado com fallbacks (ADR-0003), e isso é a maior
alavanca de tamanho e confiabilidade do pacote:

| Camada | Conteúdo | Decisão Fase 1 | Tamanho estimado |
| --- | --- | --- | --- |
| Núcleo | CPython runtime, stdlib, `openai`, `yt-dlp` | Empacotar | ~80–150 MB |
| Visão local | `opencv-python-headless` (Haar cascades) | Empacotar | ~60–100 MB |
| FFmpeg | binário estático `ffmpeg.exe`/`ffprobe.exe` | Empacotar (seção 2.3) | ~90–130 MB |
| Transcrição local | `faster-whisper` + `ctranslate2` (CPU) | Avaliar na Fase 3; padrão do beta é transcrição via OpenAI API ou legendas do YouTube | ~150–300 MB + modelo |
| YOLO | `ultralytics` + PyTorch (CPU) | **Empacotar — decisão de 2026-06-10 (Opção A)** | 2,6–4 GB |

> **Decisão registrada (2026-06-10):** o beta usa a **Opção A — pacote
> completo**, incluindo `ultralytics` + PyTorch CPU, para garantir que o Smart
> Camera/Vision Engine se comporte nos PCs dos testers exatamente como na
> máquina de desenvolvimento (que usa `yolo26n.pt`). O tamanho de ~4 GB foi
> aceito explicitamente. O repositório e a distribuição são privados, então a
> licença AGPL da Ultralytics não bloqueia o beta gratuito; ela DEVE ser
> revisitada (rota ONNX, seção abaixo) antes de qualquer distribuição
> comercial. Cada tester configura a própria chave OpenAI pela engrenagem de
> settings (SPEC-007); a chave nunca é embutida no pacote. O detalhamento está
> em [PLANO-IMPLEMENTACAO.md](PLANO-IMPLEMENTACAO.md).

Custos conhecidos de empacotar YOLO/torch (aceitos na Opção A; motivam a
rota ONNX pós-beta):

- Builds PyInstaller com torch chegam a 2,6–4 GB e há relatos de inferência
  até ~6x mais lenta depois do empacotamento.
- `ultralytics` é AGPL-3.0; redistribuir embutido em um app fechado é um
  problema de licença que o próprio ADR-0003 já mandou revisar antes de
  qualquer distribuição comercial.
- O Smart Camera já cai para OpenCV quando YOLO não carrega — é fallback de
  produto, não gambiarra. O beta valida o fluxo; YOLO continua disponível para
  o dev local.
- Caminho futuro, se a qualidade exigir: exportar um modelo de detecção de
  pessoa para **ONNX** e rodar via `onnxruntime` (license MIT, dezenas de MB,
  sem torch). Isso vira uma fase própria, fora do beta.

### 2.3 FFmpeg: bundlear binário estático, invocado por subprocess

- Fonte recomendada: build `release-essentials` do gyan.dev (inclui `libx264`,
  que o pipeline usa para H.264 + CRF). Esses builds são **GPLv3** porque
  incluem x264.
- O CUTED chama `ffmpeg.exe` como **processo separado** (subprocess), o que a
  interpretação corrente da FSF trata como "mere aggregation" — o app não
  precisa virar GPL. Obrigações que ficam:
  - incluir os textos de licença do FFmpeg em `packaging/third-party-licenses/`;
  - disponibilizar (ou linkar de forma estável) o código-fonte exato do build
    distribuído — o gyan.dev publica fonte por versão; fixar a versão usada;
  - declarar no instalador/README que o FFmpeg é software de terceiros.
- Nota explícita: isto é entendimento técnico, não aconselhamento jurídico.
  Antes de versão comercial, revisar com apoio jurídico (junto com patentes de
  codec H.264/AAC, que são tema separado de licença de software).
- O launcher deve resolver o FFmpeg na ordem: pasta do app (`./ffmpeg/`) →
  `PATH` → erro amigável. Nunca pedir para o usuário editar PATH.

### 2.4 Instalador: Inno Setup

- Inno Setup embala a pasta `onedir` num `CUTED-Setup-<versao>.exe` com:
  atalho no Menu Iniciar, atalho opcional na Área de Trabalho, desinstalador
  automático, instalação **per-user** (`{localappdata}\Programs\CUTED`) sem
  exigir admin.
- Escolhido sobre NSIS por ser declarativo, manter rastreio de desinstalação
  por padrão e ser o caminho usado por apps como VS Code; sobre MSIX por
  evitar exigência de assinatura nesta fase.
- Regra de desinstalação: **nunca apagar** `Documents/CUTED Workspace` nem
  `Videos/CUTED Renders` nem `%USERPROFILE%\.cuted`.

### 2.5 SmartScreen e assinatura

- Beta sem assinatura: o Windows vai mostrar "Windows protegeu o computador".
  Documentar para os amigos o caminho "Mais informações → Executar assim
  mesmo" com captura de tela no guia de instalação.
- Reputação SmartScreen se acumula por hash do arquivo; cada release nova
  zera. Não vale investimento agora.
- Quando for distribuição séria: certificado OV/EV ou Azure Trusted Signing —
  EV/Trusted Signing remove o aviso de imediato; OV depende de reputação
  acumulada. Custo típico de centenas de dólares/ano; decisão de produto
  pós-beta.

### 2.6 Configuração e segredos no app empacotado

- O app empacotado não tem repositório, então `.env.local` deixa de existir
  como mecanismo. A fonte de configuração passa a ser o que a SPEC-007 já
  definiu: `%USERPROFILE%\.cuted\settings.json` + chave OpenAI salva fora do
  navegador, com `CUTED_HOME` como override.
- O instalador nunca grava segredos. A primeira execução abre o app
  funcionando sem chave (importação local + presets manuais); recursos de IA
  pedem a chave pela UI de settings existente.

## 3. Arquitetura do Pacote

```text
{localappdata}\Programs\CUTED\        # instalado pelo Inno Setup
  cuted.exe                           # launcher (entrypoint PyInstaller onedir)
  _internal\                          # runtime Python + libs (PyInstaller)
  ffmpeg\
    ffmpeg.exe
    ffprobe.exe
  assets\
    brand\cuted-logo-transparent.png
  licenses\                           # FFmpeg, OpenCV, yt-dlp, etc.
  VERSION

Documents\CUTED Workspace\jobs\<job-id>\   # dados do usuário (SPEC-011)
Videos\CUTED Renders\<job-id>\             # MP4 finais
%USERPROFILE%\.cuted\                      # settings, ledger, caches de modelo
%LOCALAPPDATA%\CUTED\logs\                 # logs de runtime do launcher
```

Comportamento do `cuted.exe` (comando padrão = `launch`):

1. cria as pastas de workspace se não existirem;
2. escolhe porta livre em `127.0.0.1` (range fixo, ex.: 8779–8799);
3. valida FFmpeg e dependências; erro vira mensagem amigável + log;
4. sobe o servidor local existente (`serve`) apontando para o workspace;
5. abre o navegador padrão na URL local;
6. mantém um processo único (lock file/porta) para não duplicar servidores;
7. `cuted.exe diagnostics` gera o bundle de suporte definido na SPEC-011
   (metadados seguros, sem vídeos, sem transcrições, sem chaves).

## 4. Estrutura da pasta `packaging/` no repositório

```text
packaging/
  PLANO-EXECUTAVEL-WINDOWS.md   # este documento
  cuted.spec                    # spec do PyInstaller (onedir, hidden imports, datas)
  build.ps1                     # build reprodutível: limpa, builda, copia ffmpeg, gera VERSION
  installer.iss                 # script Inno Setup
  third-party-licenses/         # textos de licença redistribuídos
  guides/
    INSTALACAO-BETA.md          # guia com prints para os amigos (inclui SmartScreen)
  dist/                         # saída de build (ignorado pelo git)
  build/                        # intermediários do PyInstaller (ignorado pelo git)
```

Pendência para o fluxo do Codex: adicionar `packaging/dist/` e
`packaging/build/` ao `.gitignore` (não alterado por este plano para não tocar
arquivos existentes).

Atenção operacional: o repositório vive dentro do OneDrive. Builds geram
milhares de arquivos e o sync do OneDrive deixa isso lento e pode corromper
builds no meio do processo. Recomendação: rodar o build com saída fora da
pasta sincronizada (ex.: `%LOCALAPPDATA%\cuted-build`) ou marcar
`packaging/dist|build` como "sempre local"/excluído do sync.

## 5. Fases de Implementação

Mapeadas nos slices A–E da SPEC-011, com critério de aceite por fase.

### Fase 1 — Launcher local (Slice A)

- Novo entrypoint `launch` (pode viver em `packaging/` ou como subcomando novo,
  decisão do Codex) com: porta livre, criação de workspace, abertura do
  navegador, log em `%LOCALAPPDATA%\CUTED\logs`, instância única.
- Aceite: `python cutted.py launch` (ainda sem empacotar) abre o workspace do
  usuário no navegador sem argumentos.

### Fase 2 — Workspace fora do repo (Slice B)

- Jobs criados em `Documents/CUTED Workspace/jobs`; renders finais copiados
  para `Videos/CUTED Renders/<job>` (mecanismo `output_path` já existe).
- Aceite: nenhum artefato novo aparece em `samples/` durante uso normal; a
  matriz de regressão "Finalize" continua passando.

### Fase 3 — Build portátil (Slice C)

- `cuted.spec` onedir + `build.ps1`; incluir OpenCV headless e cascades Haar
  (são `datas` do pacote cv2 — ponto clássico de falha do PyInstaller);
  excluir `ultralytics`/`torch`/`matplotlib`/`pandas`/`scipy` explicitamente.
- Decidir transcrição local: começar **sem** `faster-whisper` no pacote
  (padrão: legendas do YouTube + OpenAI API, que é o fluxo já protegido por
  compressão/chunking do ADR-0002). Se o beta exigir transcrição offline,
  medir o custo de tamanho do `ctranslate2` CPU em build separado.
- Copiar `ffmpeg.exe`/`ffprobe.exe` (gyan.dev essentials, versão pinada) para
  `dist/CUTED/ffmpeg/` + licenças.
- Aceite: numa máquina **sem Python**, `dist\CUTED\cuted.exe` abre o app,
  importa um MP4 local, renderiza um TikTok final com legenda e overlay.

### Fase 4 — Instalador (Slice D)

- `installer.iss`: per-user, atalhos, desinstalador, página "instalando
  FFmpeg de terceiros", preservação dos dados do usuário no uninstall.
- Aceite: checklist da SPEC-011 (Step 9) completo numa máquina limpa,
  incluindo instalar → usar → desinstalar → renders preservados.

### Fase 5 — Hardening do beta (Slice E)

- `cuted.exe diagnostics`; controle de limpeza por job (tamanho aproximado +
  apagar caches/preview/source com confirmação); guia de instalação com
  prints (SmartScreen incluso); doc de problemas conhecidos.
- Verificação simples de versão (arquivo `VERSION` + checagem manual ou
  endpoint estático) — sem auto-update no beta.

## 6. Riscos e Mitigações

| Risco | Mitigação |
| --- | --- |
| Falso positivo de antivírus | `onedir`; sem UPX; testar no VirusTotal antes de cada release; instruções no guia |
| SmartScreen assusta testers | Print no guia; assinatura fica para fase comercial |
| PyInstaller quebra caminho de dados (cv2, cascades, certifi) | Smoke test automatizado pós-build que roda análise + render numa amostra mínima |
| Servidor antigo rodando após update (risco já documentado no runbook) | Instância única por lock; launcher mata/reaproveita processo da porta |
| Jobs gigantes lotam disco | Controles de limpeza da Fase 5 + tamanho do job visível |
| GPL/licenças do FFmpeg | Subprocess + licenças + fonte pinada; revisão jurídica antes de venda |
| AGPL da Ultralytics | Aceito no beta privado (Opção A); migrar para ONNX antes de distribuição comercial |
| Build dentro do OneDrive | Saída de build fora do sync |
| Chave OpenAI em máquina de tester | Fluxo SPEC-007 (nunca em localStorage/HTML); diagnostics não coleta segredos |

## 7. Critério de Sucesso do Beta

- Amigo leigo instala e renderiza um clipe sem nenhum suporte por chamada.
- Zero comandos de terminal em todo o fluxo.
- Instalador na configuração completa (Opção A) dentro de ~4 GB; meta de
  emagrecer para < ~400 MB na futura rota ONNX.
- Desinstalação não destrói nenhum render do usuário.
- Cada problema reportado vem acompanhado de um bundle `diagnostics`.

## 8. Fontes da Pesquisa

- PyInstaller + torch: tamanho e lentidão — github.com/pyinstaller/pyinstaller
  issues #8551, #8211 e discussion #8552; ultralytics issues #9163, #7439.
- Antivírus e onedir vs onefile — pythonguis.com/faq/problems-with-antivirus-software-and-pyinstaller;
  coderslegacy.com/pyinstaller-exe-detected-as-virus-solutions;
  pyinstaller discussion #5877.
- SmartScreen e reputação/assinatura — learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation;
  advancedinstaller.com/prevent-smartscreen-from-appearing.html.
- FFmpeg licenciamento — ffmpeg.org/legal.html; builds Windows e licença
  GPLv3 dos binários com x264 — gyan.dev/ffmpeg/builds.
- GPL "mere aggregation"/subprocess — gnu.org/licenses/old-licenses/gpl-2.0-faq
  (seções MereAggregation/GPLPlugins).
- Inno Setup vs NSIS — advancedinstaller.com/choosing-the-right-windows-packaging-tool-as-developer.html.
