# Plano de Implementação — Beta Windows CUTED (Opção A: Pacote Completo)

Status: aprovado para execução
Data: 2026-06-10
Base: [PLANO-EXECUTAVEL-WINDOWS.md](PLANO-EXECUTAVEL-WINDOWS.md),
[SPEC-011](../docs/product/SPEC-011-local-beta-installer.md)

## Decisões Registradas

- **Opção A — pacote completo**: o instalador inclui `ultralytics` + PyTorch
  CPU para que o Smart Camera/Vision Engine rode nos PCs dos testers
  exatamente como na máquina de desenvolvimento (`yolo26n.pt`). Tamanho de
  até ~4 GB aceito explicitamente.
- **Chave OpenAI é do tester**: cada pessoa cria a própria chave e configura
  pela engrenagem de settings já existente (SPEC-007). A chave nunca é
  embutida no pacote nem em código. A UI deve deixar isso explícito nos
  pontos onde a IA é necessária.
- **Importar sem valores pré-preenchidos**: o campo `Destino dos renders`
  começa vazio, o botão `Desktop` é removido e fica apenas o seletor
  `Pasta`. A pessoa escolhe onde os vídeos finais vão parar.
- **Distribuição privada**: repositório e beta são privados; a licença AGPL
  da Ultralytics fica aceita nesta fase e será revisitada (rota ONNX) antes
  de qualquer distribuição comercial.

## Princípio de Execução

Mexer o mínimo possível no código do app. Apenas as Fases 1–3 tocam
`tools/cutted/scripts/cutted.py`, cada uma com mudanças pequenas e
localizadas (âncoras de linha abaixo, válidas para o estado atual da branch
`codex/cuted-video-bumpers`). As Fases 4–6 vivem inteiramente em
`packaging/` e não alteram comportamento do app.

---

## Fase 1 — UI do Importar: chave explícita e destino vazio

Mudanças em `cutted.py` (HTML/JS embutidos):

1. **Destino dos renders vazio** (~linha 6344): remover o
   `value="{html.escape(default_desktop_path())}"` do input `output_path`;
   adicionar `placeholder="Selecione a pasta dos videos finais"`.
2. **Remover o botão Desktop**: apagar o `<button data-use-desktop>`
   (~linha 6345) e o handler JS correspondente (~linhas 9265–9271). O botão
   `Pasta` (`data-select-folder`, ~linha 6346) e o endpoint
   `/api/select-folder` (~linha 460) permanecem como único caminho.
3. **Destino obrigatório no submit do import**: se `output_path` estiver
   vazio ao iniciar um import, bloquear com mensagem amigável
   ("Escolha a pasta onde os videos finais vao ser salvos."). Justificativa:
   para testers leigos, render "perdido" dentro do workspace é chamado de
   suporte garantido.
4. **Aviso de chave OpenAI no Importar**: ao abrir a aba Importar, consultar
   `GET /api/settings/openai` (já existe). Se não houver chave configurada,
   mostrar um banner persistente no formulário de import:
   "Adicione sua chave OpenAI aqui" com botão que abre o modal da
   engrenagem (settings). O submit de import com IA sem chave mostra a mesma
   orientação em vez de erro técnico.
5. **Limpeza associada** (somente se não for usada em outro lugar):
   `default_desktop_path()` e os candidatos de Desktop (~linhas 3318–3330)
   podem ser removidos ou mantidos sem uso — decisão do implementador;
   remover é preferível para não voltar por acidente.

Documentação e testes a atualizar na mesma mudança:

- `docs/product/SPEC-002-ai-processing-tab.md`: substituir a regra
  "Default the local source path to the user's Desktop" pela regra de
  destino vazio + seletor de pasta + chave explícita.
- `docs/qa/REGRESSION_MATRIX.md`: trocar a linha "Local path defaults to
  Desktop" por: destino começa vazio; botão Desktop ausente; import sem
  destino é bloqueado com mensagem; banner de chave aparece sem chave
  configurada e abre settings.
- `tests/`: ajustar/adicionar asserts no padrão existente de inspecionar o
  HTML gerado por `page_html` (ex.: `data-use-desktop` ausente,
  placeholder presente, `value` do `output_path` vazio).

Aceite da Fase 1:

- Abrir a aba Importar sem chave configurada mostra o banner com acesso à
  engrenagem; com chave configurada, nenhum banner.
- Campo de destino vazio; só o botão `Pasta` existe; import sem destino é
  bloqueado com mensagem amigável.
- Matriz de regressão da seção "AI import UI" atualizada e passando.

## Fase 2 — Subcomando `launch` (código novo, isolado)

- Novo subcomando em `parse_args`/`main` que: cria as pastas de workspace
  (`Documents/CUTED Workspace/jobs`, `Videos/CUTED Renders`), escolhe porta
  livre em 127.0.0.1 (range 8779–8799), garante instância única (lock por
  porta/arquivo), sobe o `serve` existente apontando para o workspace, abre
  o navegador padrão e grava log em `%LOCALAPPDATA%\CUTED\logs`.
- Erros de dependência (FFmpeg ausente etc.) viram mensagem amigável no
  navegador ou em diálogo, nunca stack trace.
- Nenhuma mudança nos subcomandos existentes (`analyze`, `serve`,
  `caption-selected`, `render-selected`).

Aceite: `python tools/cutted/scripts/cutted.py launch` (ainda sem
empacotar) abre o workspace do usuário no navegador, sem argumentos, e um
segundo `launch` reaproveita a instância em vez de duplicar servidor.

## Fase 3 — Workspace padrão fora do repositório

- Quando iniciado via `launch`, novos jobs nascem em
  `Documents/CUTED Workspace/jobs/<job-id>` (o mecanismo `output_path` /
  `import-request.json` já existe; é direcionamento, não refatoração).
- `Videos/CUTED Renders` aparece apenas como sugestão visual (placeholder),
  nunca como valor pré-preenchido — coerente com a Fase 1.
- O fluxo dev com `samples/` continua intocado quando se usa `serve --dir`.

Aceite: uso normal via `launch` não cria nenhum artefato novo dentro do
repositório; checks "Finalize" da matriz de regressão continuam passando.

## Fase 4 — Build PyInstaller completo (sem tocar no app)

Arquivos novos em `packaging/`:

- `requirements-build.txt` com versões pinadas:
  - `torch` CPU-only via índice `https://download.pytorch.org/whl/cpu`
    (nunca a build CUDA — corta gigabytes e o beta não usa GPU);
  - `ultralytics`, `opencv-python-headless`, `yt-dlp`, `openai`;
  - `faster-whisper` é opcional: incluir somente se o smoke test do pacote
    passar; o beta funciona com legendas do YouTube + transcrição via API.
- `cuted.spec` (onedir, sem UPX):
  - `collect_data` de `ultralytics` (o `cfg/default.yaml` ausente é a falha
    clássica de PyInstaller com ultralytics) e dos cascades Haar do cv2;
  - excluir CUDA/`nvidia-*`; testar exclusão de `matplotlib`, `pandas`,
    `scipy` (ultralytics importa partes disso — iterar até o smoke passar);
  - incluir `yolo26n.pt` como data file do pacote.
- `build.ps1`: limpa, instala requirements pinados em venv de build, roda
  PyInstaller, copia `ffmpeg.exe`/`ffprobe.exe` (gyan.dev essentials,
  versão pinada) para `dist/CUTED/ffmpeg/`, copia licenças, grava `VERSION`.
  Saída de build fora do OneDrive (`%LOCALAPPDATA%\cuted-build`), copiando
  só o resultado final de volta se necessário.
- Modelo YOLO sem mudança de código: o launcher empacotado define
  `CUTED_YOLO_MODEL_DIR` apontando para a pasta do modelo dentro do app
  (variável já suportada pelo `cutted.py`), eliminando download na primeira
  execução.
- `smoke-test.ps1`: contra o `dist/CUTED/`, executa launch → import de um
  MP4 curto → Smart Camera (asserção: `diagnostics.vision_engine ==
  "hybrid-yolo"`) → finalize → valida MP4 final com ffprobe.

Aceite: numa máquina **sem Python**, o smoke test inteiro passa e o Smart
Camera reporta `hybrid-yolo` — essa asserção é a prova de paridade com a
máquina de desenvolvimento. Verificar o build no VirusTotal antes de
distribuir.

## Fase 5 — Instalador (Inno Setup)

- `installer.iss`: instalação per-user em `{localappdata}\Programs\CUTED`,
  atalhos Menu Iniciar + Desktop opcional, sem admin, desinstalador.
- Desinstalação **preserva** `Documents/CUTED Workspace`,
  `Videos/CUTED Renders` e `%USERPROFILE%\.cuted`.
- Tamanho esperado: ~1,5–2,5 GB comprimido, ~3–4 GB instalado.

Aceite: checklist da SPEC-011 (Step 9) completo em máquina limpa, incluindo
instalar → usar → desinstalar → renders e chave preservados.

## Fase 6 — Guia do tester e hardening

- `guides/INSTALACAO-BETA.md`, escrito para leigo, com prints:
  1. baixar e instalar (incluindo o passo SmartScreen "Mais informações →
     Executar assim mesmo");
  2. abrir o CUTED pelo Menu Iniciar;
  3. criar a chave OpenAI em platform.openai.com (passo a passo) e colar na
     engrenagem; usar o botão de testar conexão (SPEC-007);
  4. aviso claro de que o uso de IA consome créditos da chave da pessoa, com
     o ledger local de custo estimado como referência;
  5. importar o primeiro vídeo (escolher a pasta de destino) e onde
     encontrar os MP4 finais;
  6. como reportar problema: rodar `diagnostics` e enviar o arquivo gerado.
- `cuted.exe diagnostics` (SPEC-011 Step 8) e controles de limpeza por job
  (tamanho aproximado + apagar caches/preview com confirmação).

## Ordem de Execução

```text
Fase 1 (UI)  ───────────────┐
Fase 2 (launch) → Fase 3 (workspace) → Fase 4 (build) → Fase 5 (instalador)
                                          └→ Fase 6 (guia/hardening, em paralelo)
```

A Fase 1 é independente e pode ser feita primeiro como mudança pequena. As
Fases 4–6 não tocam o código do app.

## Pendências fora deste plano (para o fluxo do Codex)

- ~~Adicionar `packaging/dist/` e `packaging/build/` ao `.gitignore`.~~ Feito.
- ~~Atualizar SPEC-002 e REGRESSION_MATRIX conforme Fase 1.~~ Feito.
- Pós-beta: migração YOLO → ONNX/onnxruntime para resolver tamanho e AGPL
  antes de distribuição comercial (registrado no plano base, seção 2.2).

## Status de Execução (2026-06-10)

- Fase 1 (UI do Importar): implementada com testes (`tests/test_cutted_import_ui.py`).
- Fase 2 (`launch`): implementada e validada com smoke test local (porta livre,
  lock de instância única, recuperação de lock obsoleto, galeria bootstrap).
- Fase 3 (workspace fora do repo): implementada via `launch`.
- Fase 4 (build): artefatos prontos (`cuted_launcher.py`, `cuted.spec`,
  `build.ps1`, `requirements-build.txt`, `smoke-test.ps1`); o build em si
  precisa ser executado e iterado numa sessão dedicada.
- Fase 5 (instalador): `installer.iss` pronto; compilar após a Fase 4 passar.
- Fase 6 (guia): `guides/INSTALACAO-BETA.md` pronto, faltam os prints;
  `diagnostics` e limpeza por job continuam pendentes.

## Revisão QA (2026-06-10)

Revisão independente (agente QA) sobre as Fases 1–3 + artefatos: nenhuma
regressão no fluxo dev; 38 testes verdes. Achados corrigidos na mesma sessão:

- Bloqueante: re-execução congelada (`cuted.exe <cutted.py> analyze` e
  `cuted.exe -m yt_dlp`) tratada por shim no `cuted_launcher.py`, com testes.
- stdlib usada só pelo `cutted.py` (tkinter, http.server, webbrowser etc.)
  declarada em `hiddenimports` no spec, já que o carregamento é dinâmico.
- `multiprocessing.freeze_support()` no launcher (obrigatório com torch).
- Corrida de porta no `launch`: bind com retry em até 3 portas e navegador
  só abre depois do bind; mensagem amigável em vez de stack trace.
- Smoke test com polling (90s) em vez de sleep fixo + verificação do shim.
- `start_import_job` refatorado (`import_request_metadata`) para a regra de
  40 linhas; validações server-side cobertas por teste.
- `torch==2.12.0+cpu` pinado para nunca cair na wheel CUDA do PyPI.

Pendência consciente: o smoke automatizado não cobre import/render com vídeo
real (checklist manual no `smoke-test.ps1`). Validar na sessão de build.
