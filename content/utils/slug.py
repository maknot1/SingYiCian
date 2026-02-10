from django.utils.text import slugify
from content.models import Post, Section


def generate_post_slug(title: str) -> str:
    base = slugify(title)

    if not base:
        base = "post"

    slug = base
    counter = 1

    while Post.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1

    return slug


def generate_section_slug(title: str) -> str:
    base = slugify(title)

    if not base:
        base = "section"

    slug = base
    counter = 1

    while Section.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1

    return slug
