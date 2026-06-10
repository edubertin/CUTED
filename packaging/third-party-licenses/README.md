# Licencas de Terceiros — CUTED Beta

Esta pasta e redistribuida dentro do pacote (`licenses/`). Antes de cada
release, conferir que os textos abaixo estao presentes e atualizados.

## Obrigatorios no pacote

| Componente | Licenca | Obrigacao |
| --- | --- | --- |
| FFmpeg (build gyan.dev release-essentials) | GPLv3 (inclui libx264/libx265) | Incluir texto da licenca + registrar versao exata (`ffmpeg/VERSION.txt`); fonte do build publicada por versao em gyan.dev/ffmpeg/builds. Invocado como processo separado (mere aggregation). |
| Ultralytics + modelo YOLO | AGPL-3.0 | Aceito apenas no beta privado (decisao 2026-06-10). Migrar para ONNX/runtime permissivo antes de distribuicao comercial. |
| PyTorch | BSD-3 | Incluir aviso de copyright. |
| OpenCV | Apache-2.0 | Incluir aviso de copyright. |
| faster-whisper / CTranslate2 | MIT | Incluir aviso de copyright. |
| yt-dlp | Unlicense/Public domain | Sem obrigacao, manter referencia. |
| numpy, pillow, imageio-ffmpeg | BSD/PIL/BSD | Incluir avisos. |
| Python (CPython) | PSF-2.0 | Incluir aviso. |

## Pendencias

- [ ] Baixar e versionar os textos integrais de cada licenca nesta pasta.
- [ ] Registrar a versao exata do build FFmpeg usado em cada release.
- [ ] Revisao juridica (licencas + patentes H.264/AAC) antes de venda.

Nota: este resumo e entendimento tecnico, nao aconselhamento juridico.
