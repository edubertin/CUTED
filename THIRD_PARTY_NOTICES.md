# Software De Terceiros

CUTED depende de projetos mantidos por outras comunidades. Este resumo nao
substitui os textos integrais incluidos no pacote de build.

| Componente | Uso | Licenca principal |
| --- | --- | --- |
| Ultralytics YOLO | deteccao local de pessoas | AGPL-3.0 |
| PyTorch | runtime de inferencia | BSD-3-Clause |
| OpenCV | visao local e fallback | Apache-2.0 |
| FFmpeg/FFprobe | leitura e render de midia | LGPL/GPL, conforme o build |
| yt-dlp | importacao autorizada do YouTube | Unlicense |
| faster-whisper/CTranslate2 | transcricao local opcional | MIT |
| pywebview | janela desktop | BSD-3-Clause |
| CPython | runtime | PSF-2.0 |
| PixiJS | timeline visual | MIT |

O build atual fixa o FFmpeg `8.1.2 release-essentials` da gyan.dev, que habilita
componentes GPL. O build registra o asset imutavel, SHA-256, commit FFmpeg,
configuracao e versoes das bibliotecas externas. Uma distribuicao publica deve
disponibilizar os fontes correspondentes junto ao download ou por link estavel
no mesmo local.

O uso de Ultralytics no build atual determina a licenca AGPL-3.0 do CUTED. Quem
redistribuir uma versao modificada deve cumprir a AGPL e disponibilizar o codigo
fonte correspondente.

O script de packaging coleta automaticamente os arquivos `LICENSE`, `COPYING` e
`NOTICE` encontrados nas distribuicoes Python do ambiente de build. Revise o
diretorio `licenses/` do artefato antes de qualquer release.

O bundle de timeline incorpora PixiJS. O aviso MIT completo esta versionado em
`packaging/third-party-licenses/PixiJS-MIT.txt` e e copiado para o artefato.
