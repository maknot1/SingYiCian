import bleach

ALLOWED_TAGS = [
    "p", "br",
    "h2", "h3", "h4",
    "ul", "ol", "li",
    "strong", "em", "b", "i",
    "blockquote",
    "code", "pre",
    "img",
    "a",
    "div", "span"
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def clean_html(value: str) -> str:
    if not value:
        return ""

    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
