import re
import html

def clean_html_text(text: str) -> str:
    """
    Cleans HTML job descriptions into readable plain text.

    Handles:
    - HTML tags
    - HTML entities
    - Workday-style concatenated words
    - Whitespace normalization
    - Paragraph / line break preservation
    """

    if not text:
        return ""

    # 1. Decode HTML entities first
    text = html.unescape(text)

    # 2. Preserve structure before stripping tags
    text = re.sub(r"(?i)<\s*br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</\s*p\s*>", "\n", text)
    text = re.sub(r"(?i)<\s*/\s*li\s*>", "\n", text)
    text = re.sub(r"(?i)<\s*li[^>]*>", "- ", text)

    # 3. Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # 4. Fix non-breaking spaces + weird unicode spacing
    text = text.replace("\xa0", " ")

    # 5. Fix Workday-style concatenated words
    #    "SeniorDeveloper" → "Senior Developer"
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    #    "Developer3" → "Developer 3"
    text = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", text)
    text = re.sub(r"([0-9])([a-zA-Z])", r"\1 \2", text)

    # 6. Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # 7. Final cleanup
    return text.strip()