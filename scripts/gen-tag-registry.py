"""Генерирует таблицу тегов в docs/tag-registry.md из registry.yaml (ADR-104).

Блок между маркерами заменяется целиком; остальной файл (схема) не трогается.
Запуск: python scripts/gen-tag-registry.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from factoria.tags.registry import load_registry  # noqa: E402

DOC = ROOT / "docs" / "tag-registry.md"
BEGIN = "<!-- BEGIN GENERATED: не редактировать вручную, см. scripts/gen-tag-registry.py -->"
END = "<!-- END GENERATED -->"

COMMAND_HINT = {
    "line_start": "StartLine()",
    "line_stop": "StopLine()",
    "set_setpoint": "SetSpeed(value)",
    "switch_recipe": "SetRecipe(id)",
}


def render() -> str:
    reg = load_registry()
    rows = ["| Тег | Тип | Диапазон | Ед. | max_age, c | Запись через |",
            "|---|---|---|---|---|---|"]
    for tag in reg.tags:
        if tag.min is None and tag.max is None:
            rng = tag.enum[0] + "…" + tag.enum[-1] if tag.enum else "—"
        else:
            rng = f"{int(tag.min)}…{int(tag.max)}"
        commands = " / ".join(COMMAND_HINT.get(c, c) for c in tag.command) or "—"
        rows.append(
            f"| `{tag.id}` | {tag.type} | {rng} | {tag.unit or '—'} | "
            f"{tag.max_age_seconds:g} | {commands} |"
        )
    rows.append("")
    rows.append(
        f"Всего тегов: **{len(reg.tags)}** ({len(reg.lines)} линии × 7), "
        f"методов: **{len(reg.methods)}**."
    )
    return "\n".join(rows)


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print("маркеры не найдены в docs/tag-registry.md", file=sys.stderr)
        return 1
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{BEGIN}\n{render()}\n{END}{tail}"
    if new == text:
        print("без изменений")
        return 0
    DOC.write_text(new, encoding="utf-8", newline="\n")
    print(f"обновлено: {DOC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
