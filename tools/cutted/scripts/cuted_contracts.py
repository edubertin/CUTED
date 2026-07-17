from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Moment:
    rank: int
    start: float
    end: float
    peak: float
    score: float
    title: str
    reason: str
    transcript: str
    peak_text: str
    clip_file: str | None
    frame_file: str | None
    caption_segments: tuple[Segment, ...] = ()
    waveform_file: str | None = None
    publish_metadata: dict[str, object] | None = None
    cover_candidates: tuple[str, ...] = ()
    caption_tracks: dict[str, object] | None = None


@dataclass(frozen=True)
class CutedConfig:
    clips: int
    min_duration: float
    max_duration: float
    target_duration: float
    smart_boundaries: bool
    lead_in: float
    tail_out: float
    preset: str | None


CuttedConfig = CutedConfig


@dataclass(frozen=True)
class SourceMedia:
    render_source: str
    transcribe_source: Path | str
    label: str
    cleanup_paths: tuple[Path, ...]
    metadata: dict[str, object] | None = None


@dataclass(frozen=True)
class PublishSourceContext:
    label: str
    kind: str
    title: str
    user_context: str
    source_url: str


@dataclass(frozen=True)
class CameraAnalysisMedia:
    ref: Path | str
    cache_key: str
    label: str
    kind: str
    start: float


@dataclass(frozen=True)
class PlatformPreset:
    key: str
    label: str
    width: int
    height: int
    note: str


@dataclass(frozen=True)
class ResolutionPreset:
    key: str
    label: str
    width: int
    height: int
    destinations: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class EffectPreset:
    key: str
    label: str
    note: str


@dataclass(frozen=True)
class CameraPreset:
    key: str
    label: str
    note: str


@dataclass(frozen=True)
class OverlayPreset:
    key: str
    label: str
    title: str
    subtitle: str
    accent: str


@dataclass(frozen=True)
class CaptionEvent:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class AnimatedCaptionWindow:
    start: float
    end: float
    previous: str
    active: str
    next: str


PLATFORM_PRESETS = {
    "tiktok": PlatformPreset("tiktok", "TikTok", 1080, 1920, "9:16 vertical"),
    "shorts": PlatformPreset("shorts", "Shorts", 1080, 1920, "9:16 vertical"),
    "instagram": PlatformPreset("instagram", "Instagram", 1080, 1920, "9:16 vertical"),
    "facebook": PlatformPreset("facebook", "Facebook", 1080, 1350, "4:5 feed"),
    "youtube": PlatformPreset("youtube", "YouTube", 1920, 1080, "16:9 landscape"),
}


RESOLUTION_PRESETS = {
    "vertical_9_16": ResolutionPreset(
        "vertical_9_16", "Vertical 9:16", 1080, 1920, ("tiktok", "shorts", "instagram"), "Formato vertical compartilhado"
    ),
    "vertical_4_5": ResolutionPreset("vertical_4_5", "Vertical 4:5", 1080, 1350, ("facebook",), "Feed vertical"),
    "horizontal_16_9": ResolutionPreset("horizontal_16_9", "Horizontal 16:9", 1920, 1080, ("youtube",), "Video horizontal"),
}


PLATFORM_RESOLUTION_PRESETS = {
    destination: preset.key
    for preset in RESOLUTION_PRESETS.values()
    for destination in preset.destinations
}


DIRECTOR_INTENTS = {
    "speaker_hold": {"label": "Speaker", "subject": "primary", "transition": "hold", "reason": "Segura foco medio no speaker."},
    "group_open": {"label": "Group", "subject": "group", "transition": "hold", "reason": "Preserva o grupo, com espaco para reacoes."},
    "reaction_focus": {"label": "Reaction", "subject": "secondary", "transition": "smooth", "reason": "Realca reacao em close controlado."},
    "center_hold": {"label": "Center", "subject": "center", "transition": "hold", "reason": "Volta para o centro seguro."},
    "speaker_close": {"label": "Zoom", "subject": "primary", "transition": "smooth", "reason": "Aproxima em plano medio, sem virar so rosto."},
    "cut_focus": {"label": "Cut", "subject": "primary", "transition": "cut", "reason": "Corte seco para ritmo."},
}


EFFECT_PRESETS = {
    "none": EffectPreset("none", "Sem efeito", "Preview limpo"),
    "light-grain": EffectPreset("light-grain", "Chuvisco Leve", "Granulado sutil para tirar o aspecto cru"),
    "old-film": EffectPreset("old-film", "Filme Antigo", "Cor vintage, vinheta e textura de filme"),
    "vhs": EffectPreset("vhs", "VHS / TV Antiga", "Ruido mais forte e contraste analogico"),
    "bw-old": EffectPreset("bw-old", "Preto e Branco Antigo", "P&B com grao e vinheta"),
}


CAMERA_PRESETS = {
    "center": CameraPreset("center", "Centro seguro", "Crop limpo no centro do quadro"),
    "face-center": CameraPreset("face-center", "Rosto no centro", "Zoom leve para destacar uma pessoa central"),
    "face-left": CameraPreset("face-left", "Rosto a esquerda", "Prioriza quem esta do lado esquerdo"),
    "face-right": CameraPreset("face-right", "Rosto a direita", "Prioriza quem esta do lado direito"),
    "alternate": CameraPreset("alternate", "Alternar focos", "Movimento suave entre lados"),
    "jump-cut": CameraPreset("jump-cut", "Corte entre focos", "Troca seca entre lados, sem pan"),
    "fit-blur": CameraPreset("fit-blur", "Fit com blur", "Mostra o quadro inteiro sobre fundo desfocado"),
    "soft-zoom": CameraPreset("soft-zoom", "Zoom sutil", "Aproxima o enquadramento sem mudar o lado"),
    "punch-in": CameraPreset("punch-in", "Punch-in", "Corte mais fechado para dar energia"),
}


CAMERA_SEGMENT_PARTS = ("start", "middle", "end")
CAMERA_SEGMENT_LABELS = {"start": "Inicio", "middle": "Meio", "end": "Fim"}


OVERLAY_PRESETS = {
    "none": OverlayPreset("none", "Sem chamada", "", "", "0x000000"),
    "subscribe": OverlayPreset("subscribe", "Inscreva-se", "Inscreva-se", "Novos cortes toda semana", "0xff3b30"),
    "follow": OverlayPreset("follow", "Siga-nos", "Siga-nos", "Mais cortes no perfil", "0x24d17e"),
    "description": OverlayPreset("description", "Veja a descricao", "Veja a descricao", "Link e contexto completo", "0x4da3ff"),
    "like-share": OverlayPreset("like-share", "Curta e compartilhe", "Curta e compartilhe", "Mostre para alguem", "0xffd166"),
    "pinned-comment": OverlayPreset("pinned-comment", "Comentario fixado", "Comentario fixado", "Detalhes no primeiro comentario", "0xb388ff"),
    "watermark": OverlayPreset("watermark", "Marca d'agua", "CUTED", "clip selecionado", "0xf4f4f4"),
}
