"""Каталог шаблонов цехов (интеграция спеки Stitch, read-only)."""
from .catalog import TEMPLATES, Template, get_template, list_templates

__all__ = ["TEMPLATES", "Template", "get_template", "list_templates"]
