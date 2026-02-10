import bleach
from bleach.css_sanitizer import CSSSanitizer

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
    "*": ["class", "style"],
    "img": ["src", "alt", "title", "style"],
    "a": ["href", "title", "target", "rel"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

css_sanitizer = CSSSanitizer(
    allowed_css_properties=[
        "color",
        "background-color",

        "width",
        "max-width",
        "height",
        "float",
        "margin",
        "margin-left",
        "margin-right",
        "display",
        "text-align",
    ]
)


def clean_html(value: str) -> str:
    if not value:
        return ""

    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=css_sanitizer,
        strip=True,
    )
