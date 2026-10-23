import re


def clean_article_content(content: str | None) -> str:
    if not content:
        return ""

    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r"[ \t]+", " ", content)

    unwanted_texts = [
        "We use cookies to ensure you get the best browsing experience. "
        "By continued use, you agree to our privacy policy and accept our "
        "use of such cookies. For further information, click FIND OUT MORE.",
        "Make this your preferred source to get more updates from this "
        "publisher on Google.",
    ]

    for unwanted in unwanted_texts:
        content = content.replace(unwanted, "")

    content = re.sub(r"[ \t]+", " ", content)
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip()
