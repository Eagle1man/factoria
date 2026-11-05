"""Проверка дизайн-системы: DESIGN.md в формате skill и без запрещённого.

Ловит тихую деградацию: пропавший режим маршрута, ссылку на несуществующий
токен, секцию не в том порядке, вернувшийся градиент.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / "DESIGN.md"

SECTIONS = [
    "## Overview",
    "## Colors",
    "## Typography",
    "## Layout",
    "## Elevation & Depth",
    "## Shapes",
    "## Components",
    "## Do's and Don'ts",
]

REQUIRED_COLORS = {
    "canvas", "surface", "surface-raised", "border", "border-strong",
    "ink", "ink-muted", "ink-faint", "accent", "accent-subtle",
    "success", "warning", "danger", "info",
}

REQUIRED_ROUTES = {"/", "/production", "/approvals", "/agents", "/audit", "/settings"}

REF = re.compile(r"\{([a-z0-9.\-]+)\}")


def load():
    text = DESIGN.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "DESIGN.md должен начинаться с YAML-frontmatter"
    _, raw, body = text.split("---", 2)
    return yaml.safe_load(raw), body


def resolve(tokens: dict, path: str):
    node = tokens
    for part in path.split("."):
        assert isinstance(node, dict) and part in node, f"ссылка {{{path}}} не разрешается"
        node = node[part]
    return node


def test_frontmatter_parses_and_has_provenance():
    data, _ = load()
    assert data["provenance"] in {"decided", "extracted"}
    assert data["provenance"] == "decided"


def test_all_routes_are_operate():
    data, _ = load()
    modes = data["modes"]
    assert REQUIRED_ROUTES <= set(modes), REQUIRED_ROUTES - set(modes)
    assert set(modes.values()) == {"operate"}, modes


def test_colors_complete():
    data, _ = load()
    assert REQUIRED_COLORS <= set(data["colors"])
    assert all(isinstance(v, str) and v.startswith("#") for v in data["colors"].values())


def test_typography_has_ui_and_data_font():
    data, _ = load()
    assert data["typography"]["ui"]["family"]
    assert data["typography"]["data"]["features"] == "tabular-nums"


def test_component_references_resolve():
    data, _ = load()
    checked = 0
    for name, component in data["components"].items():
        for key, value in component.items():
            if not isinstance(value, str):
                continue
            for ref in REF.findall(value):
                resolve(data, ref)
                checked += 1
    assert checked > 20, f"проверено ссылок: {checked}"


def test_sections_in_required_order():
    _, body = load()
    positions = []
    for title in SECTIONS:
        assert title in body, f"нет секции {title}"
        positions.append(body.index(title))
    assert positions == sorted(positions), "секции идут не в том порядке"


def test_no_forbidden_decoration_in_tokens():
    data, _ = load()
    blob = repr(data).lower()
    for word in ("gradient", "linear-gradient", "radial-gradient", "backdrop-filter"):
        assert word not in blob, f"в токенах появилось {word}"


def test_variants_exist_and_declare_overrides():
    for name in ("DESIGN.operator.md", "DESIGN.chat.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "переопределя" in text.lower() or "override" in text.lower(), name


def test_vendor_styles_are_small():
    vendors = sorted(ROOT.glob("DESIGN.vendor.*.md"))
    assert 0 < len(vendors) <= 2, f"vendor-файлов: {len(vendors)}"
    for path in vendors:
        text = path.read_text(encoding="utf-8")
        assert len(text.encode("utf-8")) < 60_000, f"{path.name} слишком велик для контекста"
        assert text.lstrip().startswith("#"), f"{path.name} не похож на DESIGN.md"


def test_skill_installed():
    skill = ROOT / ".agents" / "skills" / "gradientdeck" / "SKILL.md"
    assert skill.exists(), "skill не установлен: npx gradientdeck@0.2.0 install"
    text = skill.read_text(encoding="utf-8")
    assert "GradientDeck" in text
