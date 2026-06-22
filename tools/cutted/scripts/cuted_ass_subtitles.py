from __future__ import annotations

import math
import re

from cuted_animated_captions import (
    ANIMATED_CAPTION_BOX_OPACITY,
    ANIMATED_CAPTION_BOX_SHADOW_OPACITY,
    animated_caption_canonical_window_times,
    animated_caption_render_window_times,
    animated_caption_window_events,
    animated_caption_windows_from_row,
)
from cuted_caption_text import greedy_word_chunks
from cuted_contracts import AnimatedCaptionWindow, CaptionEvent, PlatformPreset


CUTTED_CAPTION_BOTTOM_OFFSET_MULTIPLIER = 1.25


def ass_document(events: list[CaptionEvent], duration: float, preset: PlatformPreset, chars_per_line: int, max_lines: int) -> str:
    return ass_document_with_style(events, duration, preset, chars_per_line, max_lines, {})


def ass_document_with_style(
    events: list[CaptionEvent], duration: float, preset: PlatformPreset, chars_per_line: int, max_lines: int,
    row: dict[str, object]
) -> str:
    style = caption_style_from_row(row, preset)
    animated = style.get("mode") == "animated"
    dialogue = (
        ass_animated_dialogue_lines(events, duration, chars_per_line, preset, style, row)
        if animated
        else ass_dialogue_lines(events, duration, chars_per_line, max_lines)
    )
    style_lines = [ass_style_line(preset, style)]
    if animated:
        style_lines.append(ass_caption_active_style_line(preset, style))
        style_lines.append(ass_caption_side_style_line(preset, style))
        style_lines.append(ass_caption_box_style_line(preset))
    return "\n".join([
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {preset.width}",
        f"PlayResY: {preset.height}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        *style_lines,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *dialogue,
        "",
    ])


def ass_style_line(preset: PlatformPreset, style: dict[str, object] | None = None) -> str:
    style = style or {}
    mode = str(style.get("mode") or "on")
    font_size = int(style.get("size") or (72 if preset.height >= 1600 else 54))
    if mode == "animated":
        font_size = max(24, int(font_size * 0.82))
    margin_v = caption_margin_v(preset, style)
    outline = 7 if preset.height >= 1600 else 5
    primary = ass_color(str(style.get("text_color") or "#ffffff"), "00")
    background_key = "highlight_background_color" if mode == "animated" else "background_color"
    background = str(style.get(background_key) or style.get("background_color") or "transparent")
    if mode == "animated" and background == "transparent":
        background = "#000000"
    border_style = 3 if background != "transparent" else 1
    back_color = ass_color(background if background != "transparent" else "#000000", "33" if border_style == 3 else "99")
    outline_color = back_color if border_style == 3 else "&H00000000"
    return (
        "Style: Default,Arial,"
        f"{font_size},{primary},&H0000FFFF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},"
        f"{outline},0,2,80,80,{margin_v},1"
    )


def ass_caption_active_style_line(preset: PlatformPreset, style: dict[str, object]) -> str:
    base_size = int(style.get("size") or (72 if preset.height >= 1600 else 54))
    font_size = max(24, int(base_size * 0.82))
    outline = 7 if preset.height >= 1600 else 5
    primary = ass_color(str(style.get("text_color") or "#ffffff"), "00")
    return (
        "Style: CaptionActive,Arial,"
        f"{font_size},{primary},&H0000FFFF,&H66000000,&H99000000,-1,0,0,0,100,100,0,0,1,"
        f"{outline},0,5,80,80,{caption_margin_v(preset, style)},1"
    )


def ass_caption_side_style_line(preset: PlatformPreset, style: dict[str, object]) -> str:
    base_size = int(style.get("size") or (72 if preset.height >= 1600 else 54))
    font_size = max(22, int(base_size * 0.66))
    outline = 6 if preset.height >= 1600 else 4
    primary = ass_color(str(style.get("text_color") or "#ffffff"), "18")
    background = str(style.get("background_color") or "transparent")
    border_style = 3 if background != "transparent" else 1
    back_color = ass_color(background if background != "transparent" else "#000000", "33" if border_style == 3 else "99")
    outline_color = back_color if border_style == 3 else "&H00000000"
    return (
        "Style: CaptionSide,Arial,"
        f"{font_size},{primary},&H0000FFFF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},"
        f"{outline},0,5,80,80,{caption_margin_v(preset, style)},1"
    )


def ass_caption_box_style_line(preset: PlatformPreset) -> str:
    return (
        "Style: CaptionBox,Arial,"
        "1,&H00FFFFFF,&H0000FFFF,&HFF000000,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1"
    )


def caption_margin_v(preset: PlatformPreset, style: dict[str, object] | None = None) -> int:
    if style and style.get("bottom") is not None:
        return int(preset.height * clamp_float(style.get("bottom"), 6.0, 32.0, 16.0) / 100.0 + 0.5)
    base_margin = 250 if preset.height >= 1600 else 95
    return int(base_margin * CUTTED_CAPTION_BOTTOM_OFFSET_MULTIPLIER + 0.5)


def caption_style_from_row(row: dict[str, object], preset: PlatformPreset) -> dict[str, object]:
    raw = row.get("caption_style")
    if not isinstance(raw, dict):
        return {}
    mode = normalize_caption_mode(raw.get("mode") or raw.get("captionMode") or raw.get("caption_mode"))
    background = normalize_caption_background_color(raw.get("backgroundColor") or raw.get("background_color"))
    highlight = normalize_caption_background_color(
        raw.get("highlightBackgroundColor")
        or raw.get("highlight_background_color")
        or raw.get("activeBackgroundColor")
        or raw.get("active_background_color")
        or background
    )
    return {
        "size": clamp_int(raw.get("size"), 24, 140, 72 if preset.height >= 1600 else 54),
        "width": clamp_int(raw.get("width"), 12, 56, 28),
        "bottom": clamp_float(raw.get("bottom") or raw.get("height"), 6.0, 32.0, default_caption_bottom_percent(preset)),
        "mode": mode,
        "text_color": normalize_hex_color(raw.get("textColor") or raw.get("text_color"), "#ffffff"),
        "background_color": background,
        "highlight_background_color": highlight,
    }


def default_caption_bottom_percent(preset: PlatformPreset) -> float:
    return round(caption_margin_v(preset) / max(preset.height, 1) * 100.0, 2)


def normalize_caption_mode(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"animated", "animada"}:
        return "animated"
    if text in {"off", "false", "0"}:
        return "off"
    return "on"


def clamp_float(value: object, minimum: float, maximum: float, fallback: float) -> float:
    number = float(value) if isinstance(value, (int, float)) else fallback
    return min(max(number, minimum), maximum)


def clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, number))


def normalize_hex_color(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", text) else fallback


def normalize_caption_background_color(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text or text in {"none", "transparent"}:
        return "transparent"
    return normalize_hex_color(text, "#000000")


def ass_color(value: str, alpha: str) -> str:
    color = normalize_hex_color(value, "#000000").lstrip("#")
    red, green, blue = color[0:2], color[2:4], color[4:6]
    return f"&H{alpha}{blue}{green}{red}".upper()


def ass_alpha_from_opacity(opacity: float) -> str:
    alpha = int(round((1.0 - clamp(opacity, 0.0, 1.0)) * 255))
    return f"{alpha:02X}"


def ass_rgb_color(value: str) -> str:
    color = normalize_hex_color(value, "#000000").lstrip("#")
    red, green, blue = color[0:2], color[2:4], color[4:6]
    return f"&H{blue}{green}{red}&".upper()


def ass_dialogue_lines(events: list[CaptionEvent], duration: float, chars_per_line: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    for event in events:
        start = min(max(event.start, 0.0), duration)
        end = min(max(event.end, start + 0.15), duration)
        text = ass_escape_text(wrap_caption_text(event.text, chars_per_line, max_lines))
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}")
    return lines


def ass_animated_dialogue_lines(
    events: list[CaptionEvent], duration: float, chars_per_line: int, preset: PlatformPreset, style: dict[str, object],
    row: dict[str, object] | None = None,
) -> list[str]:
    lines: list[str] = []
    active_size = max(24, int(int(style.get("size") or (72 if preset.height >= 1600 else 54)) * 0.82))
    side_size = max(22, int(int(style.get("size") or active_size) * 0.66))
    center_x = preset.width // 2
    center_y = ass_animated_caption_center_y(preset, style, active_size)
    side_y = center_y + max(3, int(active_size * 0.08))
    previous_end = 0.0
    canonical_windows = animated_caption_windows_from_row(row or {}, duration)
    windows = canonical_windows or animated_caption_window_events(events, duration, chars_per_line)
    for window in windows:
        start, end = (
            animated_caption_canonical_window_times(window, duration, previous_end)
            if canonical_windows
            else animated_caption_render_window_times(window, duration, previous_end)
        )
        if end <= start:
            continue
        previous_end = end
        if window.previous:
            prev_x = int(clamp(center_x - ass_caption_side_offset(window.previous, window.active, active_size, side_size), 70, preset.width - 70))
            lines.append(ass_animated_dialogue_line(0, start, end, "CaptionSide", window.previous, prev_x, side_y, ""))
        if window.next:
            next_x = int(clamp(center_x + ass_caption_side_offset(window.next, window.active, active_size, side_size), 70, preset.width - 70))
            lines.append(ass_animated_dialogue_line(0, start, end, "CaptionSide", window.next, next_x, side_y, ""))
        pop = r"\fad(25,70)\t(0,90,\fscx112\fscy112)\t(90,190,\fscx100\fscy100)"
        lines.extend(ass_animated_caption_box_lines(start, end, window.active, center_x, center_y, active_size, style))
        lines.append(ass_animated_dialogue_line(3, start, end, "CaptionActive", window.active, center_x, center_y, pop))
    return lines


def ass_animated_caption_box_lines(
    start: float, end: float, text: str, center_x: int, center_y: int, font_size: int,
    style: dict[str, object],
) -> list[str]:
    width = int(ass_caption_word_width(text, font_size) + font_size * 0.88 + 0.5)
    height = int(font_size * 1.28 + 0.5)
    radius = max(6, int(font_size * 0.25 + 0.5))
    shape = ass_rounded_rect_path(width, height, radius)
    color = ass_rgb_color(str(style.get("highlight_background_color") or "#000000"))
    top_left_x = center_x - (width // 2)
    top_left_y = center_y - (height // 2) + max(5, int(font_size * 0.16 + 0.5))
    shadow_y = top_left_y + max(5, font_size // 9)
    shadow_alpha = ass_alpha_from_opacity(ANIMATED_CAPTION_BOX_SHADOW_OPACITY)
    fill_alpha = ass_alpha_from_opacity(ANIMATED_CAPTION_BOX_OPACITY)
    border_alpha = ass_alpha_from_opacity(0.12)
    shadow = ass_vector_dialogue_line(1, start, end, top_left_x, shadow_y, shape, "&H000000&", shadow_alpha, "", "")
    fill = ass_vector_dialogue_line(
        2, start, end, top_left_x, top_left_y, shape, color, fill_alpha, r"\fad(25,70)", rf"\bord2\3c&HFFFFFF&\3a&H{border_alpha}"
    )
    return [shadow, fill]


def ass_vector_dialogue_line(
    layer: int, start: float, end: float, x: int, y: int, shape: str, color: str, alpha: str, tags: str, border: str
) -> str:
    vector_tags = rf"{{\an7\pos({x},{y})\p1\1c{color}\1a&H{alpha}&\bord0\shad0{border}{tags}}}"
    return f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},CaptionBox,,0,0,0,,{vector_tags}{shape}"


def ass_rounded_rect_path(width: int, height: int, radius: int) -> str:
    width = max(2, width)
    height = max(2, height)
    radius = max(1, min(radius, width // 2, height // 2))
    points = ass_rounded_rect_points(width, height, radius)
    first, *rest = points
    return " ".join([f"m {first[0]} {first[1]}", *(f"l {x} {y}" for x, y in rest)])


def ass_rounded_rect_points(width: int, height: int, radius: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    corners = (
        (width - radius, radius, -90, 0),
        (width - radius, height - radius, 0, 90),
        (radius, height - radius, 90, 180),
        (radius, radius, 180, 270),
    )
    for cx, cy, start_angle, end_angle in corners:
        for step in range(5):
            angle = math.radians(start_angle + (end_angle - start_angle) * step / 4)
            points.append((int(round(cx + math.cos(angle) * radius)), int(round(cy + math.sin(angle) * radius))))
    return points


def ass_animated_dialogue_line(
    layer: int, start: float, end: float, style_name: str, text: str, x: int, y: int, tags: str
) -> str:
    text_value = ass_escape_text(text)
    position = rf"{{\an5\pos({x},{y}){tags}}}"
    return f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},{style_name},,0,0,0,,{position}{text_value}"


def ass_animated_caption_center_y(preset: PlatformPreset, style: dict[str, object], font_size: int) -> int:
    margin = caption_margin_v(preset, style)
    return int(max(font_size, preset.height - margin - (font_size * 0.55)) + 0.5)


def ass_caption_side_offset(side: str, active: str, active_size: int, side_size: int) -> int:
    active_width = ass_caption_word_width(active, active_size)
    side_width = ass_caption_word_width(side, side_size)
    gap = max(22, int(active_size * 0.62))
    return int((active_width / 2) + (side_width / 2) + gap + 0.5)


def ass_caption_word_width(text: str, font_size: int) -> float:
    wide = sum(1 for char in text if char in "mwMW@#%&")
    narrow = sum(1 for char in text if char in "ilI.,'!|")
    normal = max(len(text) - wide - narrow, 0)
    return (normal * 0.56 + wide * 0.78 + narrow * 0.28) * font_size


def wrap_caption_text(text: str, chars_per_line: int, max_lines: int) -> str:
    lines = greedy_word_chunks(text.split(), max(chars_per_line, 12))
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [" ".join(lines[max_lines - 1:])]
    return r"\N".join(lines)


def ass_escape_text(text: str) -> str:
    return text.replace("{", "(").replace("}", ")")


def ass_time(value: float) -> str:
    centiseconds = int(round(max(value, 0.0) * 100))
    hours, rem = divmod(centiseconds, 360000)
    minutes, rem = divmod(rem, 6000)
    seconds, cs = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
