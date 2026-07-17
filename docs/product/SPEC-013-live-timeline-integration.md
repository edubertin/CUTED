# SPEC-013 - Live Timeline Integration

## Objetivo

Substituir a timeline compacta atual do preview por uma timeline viva, visualmente rica e reutilizavel, sem reescrever a logica de camera, trim, audio e efeitos que ja existe no CUTED.

## Escopo

- Usar `prototypes/live-timeline` como origem do componente visual.
- Exportar uma API pequena via `createLiveTimeline`.
- Manter o app real como dono do estado.
- Converter `camera_path`, trim, playhead, waveform e futuros effects verdes por adapter.
- Integrar primeiro acima do video, onde hoje existe `data-preview-camera-timeline`.
- Mostrar uma timeline leve em cada linha da aba Editar, para que `#01`, `#02`, `#03` sejam percebidos como linhas editaveis.
- Montar a timeline Pixi viva apenas no card aberto, mantendo os cards fechados baratos.

## Fora De Escopo Inicial

- Alterar render final de efeitos por keyframe.
- Remover imediatamente o painel atual de Ajuste fino.
- Reescrever os inspectors reais de camera/effects.
- Trocar o sistema de volume existente.
- Publicar a timeline nova como produto separado.

## Modulo

Entrada publica:

```ts
createLiveTimeline(container, {
  duration,
  trimStart,
  trimEnd,
  playhead,
  keyframes,
  peaks,
  showVolume,
  callbacks
})
```

No codigo atual, o formato publico esta em:

- `prototypes/live-timeline/src/liveTimeline.ts`
- `prototypes/live-timeline/src/cuttedAdapter.ts`
- `prototypes/live-timeline/src/index.ts`

Builds:

- Demo: `npm run build`
- Biblioteca: `npm run build:lib`

## Adapter Do CUTED

O app real deve converter:

- `trimValues(card).duration` para `duration`
- `trimValues(card).trimStart` para `trimStart`
- `trimEndPosition(values)` para `trimEnd`
- `video.currentTime` ou `card.dataset.pendingSeek` para `playhead`
- `cameraPathForEdit(edit, duration)` para markers azuis
- `waveform_file` carregado pelo fluxo atual para `peaks`
- futuro `effect_keyframes` para markers verdes

Callbacks esperados:

- `onSeek(time)` chama `seekTimeline(card, time, { userInitiated: true, mode: "free" })`
- `onTrimChange({ start, end })` atualiza `trimStart` e `trimEnd`
- `onKeyframeOpen(keyframe)` abre o inspector real de camera ou effect
- `onPlayToggle(playing)` delega para o video real
- `onVolumeChange(volume, muted)` fica desabilitado no app real; volume continua no player.

## Integracao Por Linha

Cada `<details class="card">` continua sendo o dono do estado. A linha fechada recebe uma timeline leve em `data-card-row-timeline`, derivada dos mesmos dados do card:

- faixa selecionada via `trimStart`/`trimEnd`;
- pontos azuis via `camera_path`;
- playhead aproximado quando o card esta ativo;
- sem waveform pesada e sem Pixi.

Quando o card abre, `data-preview-camera-timeline` monta a timeline viva. Quando fecha, o controller e destruido. Isso evita manter varios tickers/canvas ativos em listas grandes.

## Contrato De Assets

O build de biblioteca gera:

- `prototypes/live-timeline/dist-lib/live-timeline.js`
- `prototypes/live-timeline/dist-lib/live-timeline.css`

Esses arquivos sao copiados para:

- `tools/cutted/assets/live-timeline/live-timeline.js`
- `tools/cutted/assets/live-timeline/live-timeline.css`

Durante `write_html`, o CUTED copia esses assets para a galeria em `assets/live-timeline/` e injeta o CSS/JS antes do script principal. Se os assets nao existirem, o app cai para a timeline compacta atual.

## Sequencia De Importacao

1. Copiar o bundle de `dist-lib` para os assets gerados pelo CUTED.
2. Injetar `live-timeline.css` e `live-timeline.js` no HTML gerado.
3. Trocar o corpo de `renderPreviewCameraTimeline(card)` para montar/atualizar o componente.
4. Guardar o controller no card, por exemplo `card.__liveTimeline`.
5. Habilitar visual, seek e play delegado ao video real.
6. Habilitar trim pelos handles laterais atualizando `cardState`.
7. Ligar keyframes azuis ao popover/inspector real.
8. Manter keyframes verdes como camada visual futura ate existir render final.

## Contrato Futuro De Effects

Sugestao retrocompativel:

```json
{
  "effect_keyframes": [
    {
      "time": 4.2,
      "key": "light-grain",
      "label": "Grain",
      "intensity": 0.7,
      "source": "manual-effect"
    }
  ]
}
```

Enquanto isso nao renderiza no video final, a camada verde pode existir como UI experimental sem alterar exportacao.

## Riscos

- A timeline nova trabalha melhor em tempo absoluto do clip; a timeline compacta atual trabalha muito em janela ajustada pelo trim.
- O CUTED atual gera HTML/JS a partir de Python, entao o bundle precisa ser tratado como asset estatico.
- Cards multiplos exigem lifecycle claro: montar no card ativo e destruir quando necessario.
- Pixi aumenta o custo visual; em lista grande, o componente deve ser lazy.
- O bundle da timeline aumenta o HTML gerado por assets externos. O fallback legado deve continuar funcionando.

## Aceite

- Build demo passa.
- Build lib passa e gera `live-timeline.js/css`.
- A demo continua abrindo no navegador.
- Adapter converte `camera_path`, waveform e effects sem depender do DOM real.
- Cada linha fechada da aba Editar mostra uma timeline leve.
- Card aberto monta a timeline viva e delega seek/trim/play/keyframe para o estado real.
- Sem assets da timeline, a timeline compacta atual continua funcionando.
