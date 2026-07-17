# Licencas De Terceiros - CUTED

Esta pasta e copiada para `licenses/` em todo build Windows. O CUTED e
distribuido sob AGPL-3.0; componentes de terceiros continuam sujeitos as suas
proprias licencas.

## Componentes Principais

| Componente | Licenca | Evidencia no artefato |
| --- | --- | --- |
| FFmpeg release-essentials | GPLv3 | `ffmpeg/LICENSE.txt`, `VERSION.txt` e `SOURCE.txt` |
| Ultralytics YOLO | AGPL-3.0 | licenca coletada do pacote Python |
| PyTorch | BSD-3-Clause | licenca coletada do pacote Python |
| OpenCV | Apache-2.0 | texto Apache e licenca coletada |
| faster-whisper / CTranslate2 | MIT | licencas coletadas |
| yt-dlp | Unlicense | licenca coletada |
| NumPy, Pillow, imageio-ffmpeg | BSD/PIL/BSD | licencas coletadas |
| CPython | PSF-2.0 | arquivos de licenca do runtime PyInstaller |
| PixiJS | MIT | `PixiJS-MIT.txt` |

`collect-third-party-licenses.py` varre o ambiente de build e copia arquivos
`LICENSE`, `COPYING`, `NOTICE` e `AUTHORS`, alem de gerar `manifest.json`.

## Gate De Binario Publico

Antes de publicar um instalador:

1. revisar o diretorio `licenses/` gerado;
2. anexar o fonte correspondente do FFmpeg ao mesmo release;
3. registrar checksum do instalador e do fonte;
4. repetir a revisao quando qualquer dependencia mudar.

Este resumo e tecnico e nao substitui aconselhamento juridico.
