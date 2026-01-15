from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Iterable, List, Optional, Tuple

BAND_TO_SCORE = {
    "0-20": 10,
    "20-40": 30,
    "40-60": 50,
    "60-80": 70,
    "80-100": 90,
}

def slugify(text: str) -> str:
    """
    Lowercase ASCII slug with underscores.
    Deterministic and safe for IDs.
    """
    if text is None:
        return ""
    text = str(text).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text

def stable_id(*parts: str, length: int = 16) -> str:
    raw = "||".join("" if p is None else str(p) for p in parts)
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return h[:length]

def split_list(value: object) -> List[str]:
    if value is None:
        return []
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return []
    # Normalize separators
    s = s.replace(";", ",")
    s = s.replace(" y ", ",")
    s = s.replace(" Y ", ",")
    # Some cells use underscores for map codes; keep as-is (handled elsewhere)
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]

def make_alpha_code(idx0: int) -> str:
    """
    0 -> A, 25 -> Z, 26 -> AA, ...
    """
    n = idx0
    letters = []
    while True:
        n, r = divmod(n, 26)
        letters.append(chr(ord("A") + r))
        if n == 0:
            break
        n -= 1
    return "".join(reversed(letters))

def parse_range_to_minmax(range_str: object) -> Tuple[Optional[float], Optional[float]]:
    if range_str is None:
        return None, None
    s = str(range_str).strip()
    if not s or s.lower() == "nan":
        return None, None
    s = s.replace(",", ".")
    # "< 1.5"
    m = re.match(r"^<\s*([0-9]+(?:\.[0-9]+)?)", s)
    if m:
        return 0.0, float(m.group(1))
    # "2.6 - 5" or "1 - 3"
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    # Fallback: single number
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", s)
    if m:
        v = float(m.group(1))
        return v, v
    return None, None

def band_to_score(value: object) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    s = s.replace(" ", "")
    if s.lower() == "nan" or not s:
        return None
    # normalize "0–20" variants
    s = s.replace("–", "-").replace("—", "-")
    return BAND_TO_SCORE.get(s)
