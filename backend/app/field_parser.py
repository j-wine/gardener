import pandas as pd
import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Normalize broken Unicode characters to ASCII (e.g., from Excel or inconsistent encodings)."""
    if pd.isna(text):
        return ""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def parse_list_column(value: str) -> list[str]:
    """Basic parser for comma-separated values (e.g., COMNAME, CAT, CLIZ)."""
    if pd.isna(value) or value.strip() == "":
        return []
    value = normalize_unicode(value)
    parts = [p.strip().lower() for p in value.split(",")]
    return [p for p in parts if p]


def parse_categorical_with_notes(value: str) -> list[str]:
    """
    Extract categorical labels before any parentheses.
    E.g., "well (dry spells), poorly (saturated)" → ["well", "poorly"]
    """
    if pd.isna(value) or value.strip() == "":
        return []

    categories = []
    for p in value.split(","):
        p = p.strip().lower()
        match = re.match(r"([a-z\s/+-]+)", p)
        if match:
            clean = match.group(1).strip()
            if clean:
                categories.append(clean)
    return categories


def get_full_category_description(value: str) -> list[str]:
    """
    Keeps the full original text segments (including parentheses).
    E.g., "well (dry spells)" → ["well (dry spells)"]
    """
    if pd.isna(value) or value.strip() == "":
        return []
    return [p.strip() for p in value.split(",") if p.strip()]
