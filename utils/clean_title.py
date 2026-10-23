import re

def clean_title(title: str) -> str:
    if not title:
        return ""

    title = re.sub(r"\s+", " ", title).strip()

    title = re.sub(
        r"\s+\b[A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4}\s+"
        r"\d{1,2}:\d{2}\s*(?:AM|PM)\b.*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    return title.strip()
