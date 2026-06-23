from __future__ import annotations

import math
import re

from cuted_caption_text import clean_caption_text
from cuted_contracts import AnimatedCaptionWindow, CaptionEvent


ANIMATED_CAPTION_LEAD_SECONDS = 0.14
ANIMATED_CAPTION_MIN_RENDER_SECONDS = 0.22
ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS = 0.24
ANIMATED_CAPTION_FAST_WORD_SECONDS = 0.20
ANIMATED_CAPTION_MAX_GROUP_WORDS = 3
ANIMATED_CAPTION_BOX_OPACITY = 0.80
ANIMATED_CAPTION_BOX_SHADOW_OPACITY = 0.28

ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS = {
    "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das", "do", "dos",
    "e", "ou", "mas", "porque", "por", "para", "pra", "com", "sem", "em", "no", "na",
    "nos", "nas", "ao", "aos", "aí", "ai", "então", "entao", "só", "so", "que", "quem",
    "qual", "quando", "onde", "como", "isso", "essa", "esse", "isto", "esta", "este",
    "eu", "tu", "ele", "ela", "nós", "nos", "vocês", "voces", "você", "voce", "meu",
    "minha", "seu", "sua", "me", "te", "se", "lhe", "não", "nao", "sim", "é", "eh",
    "foi", "era", "ser", "ter", "tem", "tá", "ta", "tava", "vai", "vou", "vão", "vao",
    "fui", "faz", "fazer", "dá", "da", "dar", "precisa", "preciso", "precisava", "acho",
    "tipo", "cara", "né", "ne", "olha", "bom", "certo", "agora",
}

ANIMATED_CAPTION_FILLER_WORDS = {
    "ah", "aham", "uhum", "hum", "eh", "é", "e", "aí", "ai", "então", "entao",
    "tipo", "assim", "né", "ne", "cara", "mano", "bom", "olha", "certo",
}

ANIMATED_CAPTION_ATTACH_PREVIOUS: set[str] = set()

ANIMATED_CAPTION_ATTACH_NEXT = {
    "a", "as", "o", "os", "um", "uma", "uns", "umas", "me", "te", "se", "meu", "minha", "seu", "sua",
    "de", "da", "das", "do", "dos", "com", "sem", "pra", "para", "por", "em", "no", "na", "nos", "nas", "ao", "aos",
}


def clean_animated_caption_text(text: str) -> str:
    clean = clean_caption_text(text)
    proper_nouns = animated_caption_proper_nouns(clean)
    words = [animated_caption_display_word(word, proper_nouns) for word in clean.split()]
    return " ".join(word for word in words if word)


def animated_caption_proper_nouns(text: str) -> set[str]:
    matches = list(re.finditer(r"[\wÀ-ÖØ-öø-ÿ]+", text, flags=re.UNICODE))
    result: set[str] = set()
    for index, match in enumerate(matches):
        word = match.group(0)
        if not animated_caption_is_capitalized_word(word):
            continue
        key = animated_caption_word_key(word)
        if key in ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS:
            continue
        sentence_start = match.start() == 0 or bool(re.search(r"[.!?…]\s*$", text[:match.start()]))
        previous_capitalized = index > 0 and animated_caption_is_capitalized_word(matches[index - 1].group(0))
        next_capitalized = index + 1 < len(matches) and animated_caption_is_capitalized_word(matches[index + 1].group(0))
        if not sentence_start or previous_capitalized or next_capitalized:
            result.add(key)
    return result


def animated_caption_display_word(word: str, proper_nouns: set[str]) -> str:
    clean = animated_caption_clean_word(word)
    if not clean:
        return ""
    key = animated_caption_word_key(clean)
    if animated_caption_is_acronym(clean) or key in proper_nouns:
        return clean
    return clean.lower()


def animated_caption_clean_word(word: str) -> str:
    clean = re.sub(r"[^\wÀ-ÖØ-öø-ÿ.,:%]+", "", word, flags=re.UNICODE)
    result: list[str] = []
    for index, char in enumerate(clean):
        if char in ".,:":
            previous_digit = index > 0 and clean[index - 1].isdigit()
            next_digit = index + 1 < len(clean) and clean[index + 1].isdigit()
            if previous_digit and next_digit:
                result.append(char)
            continue
        if char == "%":
            if index > 0 and clean[index - 1].isdigit():
                result.append(char)
            continue
        result.append(char)
    return "".join(result)


def animated_caption_word_key(word: str) -> str:
    return re.sub(r"[^\wÀ-ÖØ-öø-ÿ]+", "", word, flags=re.UNICODE).casefold()


def animated_caption_is_capitalized_word(word: str) -> bool:
    letters = [char for char in word if char.isalpha()]
    return bool(letters) and letters[0].isupper() and not animated_caption_is_acronym(word)


def animated_caption_is_acronym(word: str) -> bool:
    letters = [char for char in word if char.isalpha()]
    return 1 < len(letters) <= 6 and "".join(letters).isupper()


def animated_caption_is_numeric_token(word: str) -> bool:
    return bool(re.search(r"\d", word))


def animated_caption_is_low_value_word(word: str) -> bool:
    return animated_caption_word_key(word) in ANIMATED_CAPTION_FILLER_WORDS


def smart_animated_caption_words(text: str, max_word_length: int, duration: float) -> list[str]:
    words = split_animated_caption_words(text, max_word_length)
    if not words:
        return []
    words = smart_animated_caption_drop_fillers(words, duration)
    return smart_animated_caption_group_words(words, duration)


def smart_animated_caption_drop_fillers(words: list[str], duration: float) -> list[str]:
    word_seconds = duration / max(len(words), 1)
    if word_seconds >= ANIMATED_CAPTION_FAST_WORD_SECONDS:
        return words
    filtered = [word for word in words if animated_caption_is_numeric_token(word) or not animated_caption_is_low_value_word(word)]
    return filtered or words


def smart_animated_caption_group_words(words: list[str], duration: float) -> list[str]:
    word_seconds = duration / max(len(words), 1)
    if word_seconds >= ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS:
        return words
    groups: list[str] = []
    for word in words:
        if smart_animated_caption_should_attach_to_previous(groups, word):
            groups[-1] = f"{groups[-1]} {word}"
            continue
        if smart_animated_caption_should_attach_next(groups, words):
            groups.append(word)
            continue
        groups.append(word)
    return smart_animated_caption_balance_groups(groups)


def smart_animated_caption_should_attach_to_previous(groups: list[str], word: str) -> bool:
    if not groups:
        return False
    key = animated_caption_word_key(word)
    if key in ANIMATED_CAPTION_ATTACH_PREVIOUS:
        return smart_animated_caption_group_size(groups[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS
    previous = groups[-1].split()[-1]
    if animated_caption_word_key(previous) in ANIMATED_CAPTION_ATTACH_NEXT:
        return smart_animated_caption_group_size(groups[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS
    return key == animated_caption_word_key(previous) and smart_animated_caption_group_size(groups[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS


def smart_animated_caption_should_attach_next(groups: list[str], words: list[str]) -> bool:
    index = sum(smart_animated_caption_group_size(group) for group in groups)
    if index >= len(words):
        return False
    return animated_caption_word_key(words[index]) in ANIMATED_CAPTION_ATTACH_NEXT and index + 1 < len(words)


def smart_animated_caption_balance_groups(groups: list[str]) -> list[str]:
    result: list[str] = []
    for group in groups:
        key = animated_caption_word_key(group)
        if result and key in ANIMATED_CAPTION_ATTACH_PREVIOUS and smart_animated_caption_group_size(result[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS:
            result[-1] = f"{result[-1]} {group}"
            continue
        result.append(group)
    return result


def smart_animated_caption_group_size(group: str) -> int:
    return len([word for word in group.split() if word])


def animated_caption_windows_from_row(row: dict[str, object], duration: float) -> list[AnimatedCaptionWindow]:
    raw = row.get("animated_caption_windows")
    if not isinstance(raw, list):
        return []
    windows: list[AnimatedCaptionWindow] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        active = clean_animated_caption_text(str(item.get("active") or ""))
        if not active:
            continue
        start = clamp_float(item.get("start"), 0.0, duration, 0.0)
        end = clamp_float(item.get("end"), 0.0, duration, start)
        if end <= start:
            continue
        previous = clean_animated_caption_text(str(item.get("previous") or ""))
        next_text = clean_animated_caption_text(str(item.get("next") or ""))
        windows.append(AnimatedCaptionWindow(round(start, 3), round(end, 3), previous, active, next_text))
    return sorted(windows, key=lambda window: (window.start, window.end))


def animated_caption_canonical_window_times(
    window: AnimatedCaptionWindow, duration: float, previous_end: float = 0.0
) -> tuple[float, float]:
    start = min(max(window.start, previous_end, 0.0), duration)
    end = min(max(window.end, start + 0.08), duration)
    return round(start, 3), round(end, 3)


def animated_caption_render_window_times(
    window: AnimatedCaptionWindow, duration: float, previous_end: float = 0.0
) -> tuple[float, float]:
    raw_start = min(max(window.start, 0.0), duration)
    raw_end = min(max(window.end, raw_start + ANIMATED_CAPTION_MIN_RENDER_SECONDS), duration)
    raw_duration = max(raw_end - raw_start, ANIMATED_CAPTION_MIN_RENDER_SECONDS)
    start = min(max(raw_start - ANIMATED_CAPTION_LEAD_SECONDS, 0.0), duration)
    end = min(max(raw_end - ANIMATED_CAPTION_LEAD_SECONDS, start + ANIMATED_CAPTION_MIN_RENDER_SECONDS), duration)
    if raw_start <= ANIMATED_CAPTION_LEAD_SECONDS:
        end = min(max(end, start + raw_duration), duration)
    if start < previous_end:
        start = min(previous_end, duration)
        end = min(max(end, start + ANIMATED_CAPTION_MIN_RENDER_SECONDS), duration)
    return round(start, 3), round(end, 3)


def animated_caption_word_events(events: list[CaptionEvent], duration: float, chars_per_line: int) -> list[CaptionEvent]:
    result: list[CaptionEvent] = []
    max_word_length = max(8, min(chars_per_line, 18))
    for event in events:
        start = clamp_float(event.start, 0.0, duration, 0.0)
        end = clamp_float(event.end, start + 0.12, duration, start + 0.12)
        words = smart_animated_caption_words(event.text, max_word_length, end - start)
        if not words:
            continue
        for index, word, word_start, word_end in animated_caption_word_timings(words, start, end):
            if word_end - word_start >= 0.08:
                result.append(CaptionEvent(round(word_start, 3), round(word_end, 3), word))
    return result


def animated_caption_word_timings(words: list[str], start: float, end: float) -> list[tuple[int, str, float, float]]:
    duration = max(end - start, 0.12)
    weights = [animated_caption_word_weight(word) for word in words]
    total = sum(weights) or float(len(words) or 1)
    cursor = start
    timings: list[tuple[int, str, float, float]] = []
    for index, word in enumerate(words):
        word_end = end if index == len(words) - 1 else min(end, cursor + (duration * weights[index] / total))
        timings.append((index, word, cursor, word_end))
        cursor = word_end
    return merge_fast_animated_caption_timings(timings)


def merge_fast_animated_caption_timings(
    timings: list[tuple[int, str, float, float]]
) -> list[tuple[int, str, float, float]]:
    groups = [{"word": word, "start": start, "end": end} for _, word, start, end in timings]
    while len(groups) > 1:
        index = next(
            (
                current
                for current, group in enumerate(groups)
                if float(group["end"]) - float(group["start"]) < ANIMATED_CAPTION_MIN_RENDER_SECONDS
            ),
            -1,
        )
        if index < 0:
            break
        target = index + 1 if index + 1 < len(groups) else index - 1
        first_index, second_index = sorted((index, target))
        first = groups[first_index]
        second = groups[second_index]
        merged = {
            "word": f'{first["word"]} {second["word"]}',
            "start": first["start"],
            "end": second["end"],
        }
        groups[first_index:second_index + 1] = [merged]
    return [
        (index, str(group["word"]), float(group["start"]), float(group["end"]))
        for index, group in enumerate(groups)
    ]


def animated_caption_word_weight(word: str) -> float:
    core = re.sub(r"\W+", "", word, flags=re.UNICODE)
    return max(0.7, min(math.sqrt(max(len(core), 1)), 3.0))


def animated_caption_window_events(events: list[CaptionEvent], duration: float, chars_per_line: int) -> list[AnimatedCaptionWindow]:
    result: list[AnimatedCaptionWindow] = []
    max_word_length = max(8, min(chars_per_line, 18))
    for event in events:
        start = clamp_float(event.start, 0.0, duration, 0.0)
        end = clamp_float(event.end, start + 0.12, duration, start + 0.12)
        words = smart_animated_caption_words(event.text, max_word_length, end - start)
        if not words:
            continue
        timings = animated_caption_word_timings(words, start, end)
        for index, word, word_start, word_end in timings:
            if word_end - word_start < 0.08:
                continue
            result.append(AnimatedCaptionWindow(
                round(word_start, 3),
                round(word_end, 3),
                timings[index - 1][1] if index > 0 else "",
                word,
                timings[index + 1][1] if index + 1 < len(timings) else "",
            ))
    return result


def split_animated_caption_words(text: str, max_word_length: int) -> list[str]:
    words = [word.strip() for word in re.split(r"\s+", clean_animated_caption_text(text)) if word.strip()]
    return [word if len(word) <= max_word_length else f"{word[:max_word_length - 1]}..." for word in words]


def clamp_float(value: object, minimum: float, maximum: float, fallback: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, parsed))
