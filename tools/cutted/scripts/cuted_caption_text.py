from __future__ import annotations

import re

from cuted_contracts import CaptionEvent


CAPTION_MOJIBAKE_REPLACEMENTS = {
    "\u00c3\u00a1": "\u00e1",
    "\u00c3\u00a0": "\u00e0",
    "\u00c3\u00a2": "\u00e2",
    "\u00c3\u00a3": "\u00e3",
    "\u00c3\u00a4": "\u00e4",
    "\u00c3\u00a9": "\u00e9",
    "\u00c3\u00aa": "\u00ea",
    "\u00c3\u00ad": "\u00ed",
    "\u00c3\u00b3": "\u00f3",
    "\u00c3\u00b4": "\u00f4",
    "\u00c3\u00b5": "\u00f5",
    "\u00c3\u00ba": "\u00fa",
    "\u00c3\u00bc": "\u00fc",
    "\u00c3\u00a7": "\u00e7",
    "\u00c3\u0081": "\u00c1",
    "\u00c3\u0080": "\u00c0",
    "\u00c3\u0082": "\u00c2",
    "\u00c3\u0083": "\u00c3",
    "\u00c3\u0089": "\u00c9",
    "\u00c3\u008a": "\u00ca",
    "\u00c3\u008d": "\u00cd",
    "\u00c3\u0093": "\u00d3",
    "\u00c3\u0094": "\u00d4",
    "\u00c3\u0095": "\u00d5",
    "\u00c3\u009a": "\u00da",
    "\u00c3\u009c": "\u00dc",
    "\u00c3\u0087": "\u00c7",
    "\u00c2\u00ba": "\u00ba",
    "\u00c2\u00aa": "\u00aa",
    "\u00c2\u00b7": "\u00b7",
    "\u00c2\u00b4": "\u00b4",
}


def caption_duration(row: dict[str, object]) -> float:
    duration = float(row.get("adjusted_duration") or 0.0)
    if duration > 0:
        return duration
    start = float(row.get("adjusted_start") or row.get("start") or 0.0)
    end = float(row.get("adjusted_end") or row.get("end") or 0.0)
    return max(end - start, 0.1)


def caption_source_text(row: dict[str, object]) -> str:
    transcript = str(row.get("transcript") or "").strip()
    if transcript:
        return clean_caption_text(transcript)
    fallback = str(row.get("peak_text") or row.get("title") or "Legenda do corte")
    return clean_caption_text(fallback)


def caption_events(row: dict[str, object], chars_per_line: int, max_lines: int, duration: float) -> list[CaptionEvent]:
    segment_events = caption_events_from_segments(row, chars_per_line, max_lines)
    if segment_events:
        return normalize_caption_events(segment_events, duration)
    text = caption_source_text(row)
    chunks = caption_chunks(text, chars_per_line, max_lines, duration)
    return normalize_caption_events(distributed_caption_events(chunks, duration), duration)


def caption_events_from_segments(row: dict[str, object], chars_per_line: int, max_lines: int) -> list[CaptionEvent]:
    segments = row.get("caption_segments")
    if not isinstance(segments, list):
        return []
    start = float(row.get("adjusted_start") or row.get("start") or 0.0)
    fallback_end = start + float(row.get("adjusted_duration") or 0.0)
    end = float(row.get("adjusted_end") or row.get("end") or fallback_end)
    events = [event_from_segment(item, start, end, chars_per_line, max_lines) for item in segments]
    return [event for event in events if event is not None]


def event_from_segment(
    item: object, clip_start: float, clip_end: float, chars_per_line: int, max_lines: int
) -> CaptionEvent | None:
    if not isinstance(item, dict):
        return None
    start = max(float(item.get("start") or 0.0), clip_start) - clip_start
    end = min(float(item.get("end") or 0.0), clip_end) - clip_start
    text = clean_caption_text(str(item.get("text") or ""))
    if not text or end <= start:
        return None
    return CaptionEvent(round(start, 3), round(max(end, start + 0.35), 3), text)


def normalize_caption_events(events: list[CaptionEvent], duration: float) -> list[CaptionEvent]:
    sorted_events = sorted(events, key=lambda event: (event.start, event.end))
    normalized: list[CaptionEvent] = []
    for index, event in enumerate(sorted_events):
        start = clamp(event.start, 0.0, duration)
        end = clamp(event.end, start, duration)
        if index + 1 < len(sorted_events):
            next_start = clamp(sorted_events[index + 1].start, 0.0, duration)
            end = min(end, max(start, next_start - 0.04))
        if end - start >= 0.12:
            normalized.append(CaptionEvent(round(start, 3), round(end, 3), event.text))
    return normalized


def distributed_caption_events(chunks: list[str], duration: float) -> list[CaptionEvent]:
    slot = duration / max(len(chunks), 1)
    events: list[CaptionEvent] = []
    for index, chunk in enumerate(chunks):
        start = index * slot
        end = duration if index == len(chunks) - 1 else (index + 1) * slot
        events.append(CaptionEvent(round(start, 3), round(end, 3), chunk))
    return events


def clean_caption_text(text: str) -> str:
    clean = normalize_caption_symbols(text)
    clean = re.sub(r"(^|\s)(>{1,3}|-{1,2})\s*", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    clean = re.sub(r" ([,.;:!?])", r"\1", clean)
    clean = re.sub(r"(\d)([.,:])\s+(?=\d)", r"\1\2", clean)
    clean = re.sub(r"([,.;:!?])([^\s,.;:!?])", space_after_caption_punctuation, clean)
    clean = re.sub(r"^(nÃ©\??|aham|uhum|hum|entÃ£o|mas)\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\w+)(\s+\1\b){2,}", r"\1", clean, flags=re.IGNORECASE)
    return clean.strip(" -")


def space_after_caption_punctuation(match: re.Match[str]) -> str:
    punctuation, next_char = match.group(1), match.group(2)
    previous_index = match.start(1) - 1
    previous_char = match.string[previous_index] if previous_index >= 0 else ""
    if punctuation in ".,:" and previous_char.isdigit() and next_char.isdigit():
        return f"{punctuation}{next_char}"
    return f"{punctuation} {next_char}"


def repair_caption_encoding(text: str) -> str:
    mapped_direct = replace_caption_mojibake_sequences(text)
    if mapped_direct != text:
        return mapped_direct
    if not any(marker in text for marker in ("Ãƒ", "Ã‚", "Ã¢")):
        return text
    candidate = repair_caption_encoding_as_utf8(text)
    mapped = replace_caption_mojibake_sequences(candidate)
    return mapped if caption_mojibake_score(mapped) <= caption_mojibake_score(text) else text


def repair_caption_encoding_as_utf8(text: str) -> str:
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if caption_mojibake_score(repaired) < caption_mojibake_score(text) else text


def replace_caption_mojibake_sequences(text: str) -> str:
    clean = text
    for source, target in CAPTION_MOJIBAKE_REPLACEMENTS.items():
        clean = clean.replace(source, target)
    return clean


def caption_mojibake_score(text: str) -> int:
    return sum(text.count(marker) for marker in ("Ãƒ", "Ã‚", "Ã¢â‚¬", "Ã¢â„¢", "ï¿½"))


def normalize_caption_symbols(text: str) -> str:
    text = repair_caption_encoding(text)
    return (
        text.replace("â€œ", '"').replace("â€", '"').replace("â€˜", "'").replace("â€™", "'")
        .replace("â€¦", "...").replace("â™ª", " ").replace("\ufeff", " ")
        .replace("â€“", "-").replace("â€”", "-")
    )


def caption_chunks(text: str, chars_per_line: int, max_lines: int, duration: float) -> list[str]:
    capacity = max(18, chars_per_line * max_lines)
    chunks = greedy_word_chunks(text.split(), capacity)
    limit = max(1, int(max(duration, 1.0) / 1.35))
    if len(chunks) > limit:
        chunks = chunks[:limit]
        chunks[-1] = ellipsize_caption(chunks[-1])
    return chunks or ["Legenda do corte"]


def greedy_word_chunks(words: list[str], capacity: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and len(candidate) > capacity:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks


def ellipsize_caption(text: str) -> str:
    clean = text.rstrip(" .,;:")
    return f"{clean}..." if clean else "..."


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
