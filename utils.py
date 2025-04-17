import re

def extract_text_to_reverse(text: str) -> str:
    """Extract first quoted string from input text if LLM fails."""
    match = re.search(r"'([^']+)'|\"([^\"]+)\"", text)
    return match.group(1) or match.group(2) if match else ""

def extract_date_fallback(text: str) -> str:
    """Extracts first YYYY-MM-DD date from input text if model fails."""
    match = re.search(r"\b(20[2-9][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b", text)
    return match.group(0) if match else ""

def clean_extracted_text(text: str) -> str:
    # If surrounded in single or double quotes, strip them
    if text.startswith(("'", '"')) and text.endswith(("'", '"')):
        return text[1:-1]
    
    # If text contains a quoted string, extract first occurrence
    quoted_match = re.search(r"'([^']+)'|\"([^\"]+)\"", text)
    if quoted_match:
        return quoted_match.group(1) or quoted_match.group(2)
    
    # Fallback to full text
    return text.strip()
