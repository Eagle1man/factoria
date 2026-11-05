"""Генерирует frontend/src/scene/bindings.ts из registry.yaml (ТЗ §8.2).

Ручное редактирование результата запрещено. Запуск:
    python scripts/gen-bindings.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from factoria.tags.registry import load_registry  # noqa: E402

OUT = ROOT / "frontend" / "src" / "scene" / "bindings.ts"

# Правило привязки: тег -> (режим, суффикс меша)
RULES = {
    "Speed.PV": ("spin", "rotor"),
    "Temp.PV": ("heat", "body"),
    "Running": ("visibility", "indicator"),
    "Load.Pct": ("label", "label"),
}

HEADER = """// СГЕНЕРИРОВАНО из backend/src/factoria/tags/registry.yaml.
// Не редактировать вручную: python scripts/gen-bindings.py

export type BindingMode = 'spin' | 'heat' | 'visibility' | 'label';

export interface Binding {
  mesh: string;
  tag: TagId;
  mode: BindingMode;
}
"""


def main() -> int:
    reg = load_registry()
    lines = [HEADER, "export const TAGS = ["]
    for tag in reg.tags:
        lines.append(f"  '{tag.id}',")
    lines.append("] as const;")
    lines.append("")
    lines.append("export type TagId = (typeof TAGS)[number];")
    lines.append("")
    lines.append("export const BINDINGS: Binding[] = [")
    count = 0
    for tag in reg.tags:
        rule = RULES.get(tag.name)
        if not rule:
            continue
        mode, mesh = rule
        lines.append(f"  {{ mesh: '{tag.line}.{mesh}', tag: '{tag.id}', mode: '{mode}' }},")
        count += 1
    lines.append("];")
    lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"обновлено: {OUT} (привязок: {count}, тегов: {len(reg.tags)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
