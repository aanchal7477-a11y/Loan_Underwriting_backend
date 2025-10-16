import re
from datetime import datetime

def normalize_date(date_str: str):
    """Convert date to YYYY-MM-DD format if possible."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            return date_str  # return as-is if parsing fails

def safe_float(value):
    """Convert value to float safely."""
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except Exception:
        return None

def clean_int(value):
    """Convert value to int safely."""
    try:
        return int(re.sub(r"[^\d]", "", str(value)))
    except Exception:
        return None

def extract_fields(doc_json: dict) -> dict:
    """Extract key-value fields from Document AI JSON response."""
    fields = {}
    try:
        for entity in doc_json.get("entities", []):
            key = entity.get("type_", "").strip()
            value = entity.get("mention_text", "").strip()
            if key:
                fields[key] = value
    except Exception:
        pass
    return fields

def safe_int(value):
    try:
        if value is None:
            return None
        # Remove any non-digit characters
        cleaned = "".join(filter(str.isdigit, str(value)))
        return int(cleaned) if cleaned else None
    except Exception:
        return None

