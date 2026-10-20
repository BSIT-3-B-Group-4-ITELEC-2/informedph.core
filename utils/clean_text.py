import html
import re
from bs4 import BeautifulSoup

def clean_text(text):
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text