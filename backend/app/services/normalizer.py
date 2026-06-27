import re


_SPACES_RE = re.compile(r"\s+")
_REPEATED_CHARS_RE = re.compile(r"(.)\1{2,}", re.IGNORECASE)
_REPEATED_PUNCT_RE = re.compile(r"([!?.:,;])\1+")
_KEEP_CHARS_RE = re.compile(r"[^\w\s!?.:,;\-]+", re.UNICODE)

_LATIN_TO_CYR = str.maketrans(
    {
        "a": "а",
        "b": "в",
        "c": "с",
        "e": "е",
        "h": "н",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "t": "т",
        "x": "х",
        "y": "у",
    }
)


class TextNormalizer:
    def __init__(self, max_length: int = 512):
        self.max_length = max_length

    def normalize(self, text: str) -> str:
        cleaned = (text or "").lower().strip()
        cleaned = cleaned.translate(_LATIN_TO_CYR)
        cleaned = _KEEP_CHARS_RE.sub(" ", cleaned)
        cleaned = _REPEATED_CHARS_RE.sub(r"\1", cleaned)
        cleaned = _REPEATED_PUNCT_RE.sub(r"\1", cleaned)
        cleaned = _SPACES_RE.sub(" ", cleaned).strip()
        return cleaned[: self.max_length]

