import re
from django.utils.html import escape
from django.utils.text import Truncator
from django.utils.html import strip_tags

def make_snippet(text: str, query: str, radius: int = 80) -> str:
    if not text or not query:
        return ""

    # 1. Убираем HTML полностью
    plain = strip_tags(text)

    q = query.strip()
    if not q:
        return ""

    # 2. Ищем без учёта регистра
    match = re.search(re.escape(q), plain, re.IGNORECASE)
    if not match:
        return ""

    start = max(match.start() - radius, 0)
    end = min(match.end() + radius, len(plain))

    snippet = plain[start:end]

    if start > 0:
        snippet = "…" + snippet
    if end < len(plain):
        snippet += "…"

    # 3. Экранируем (на всякий)
    snippet = escape(snippet)

    # 4. Подсветка
    snippet = re.sub(
        f"({re.escape(q)})",
        r"<mark>\1</mark>",
        snippet,
        flags=re.IGNORECASE
    )

    return snippet
