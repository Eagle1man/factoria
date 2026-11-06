"""Цифровой двойник: срез реестра и кэша со статусом EXPERIMENTAL (ТЗ §8.5, §18.5).

Двойник здесь — не обученная модель, а проверяемое представление структуры
и текущего качества данных. Точность не измеряется и не выдумывается:
пока нет валидированного набора, в отчёте стоит null и предупреждение.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from factoria.model.semantic import SemanticModel


def twin_version(registry) -> str:
    payload = json.dumps(
        [
            registry.version if hasattr(registry, "version") else 1,
            registry.namespace,
            [tag.id for tag in registry.tags],
            sorted(registry.thresholds.items()),
        ],
        sort_keys=True,
        ensure_ascii=False,
    ).encode()
    return f"twin-{hashlib.sha256(payload).hexdigest()[:8]}"


def build_twin(registry, cache, model: SemanticModel) -> dict[str, Any]:
    snapshot = cache.snapshot()
    values: dict[str, dict[str, Any]] = snapshot["values"]
    now = datetime.now(timezone.utc)

    total = len(registry.tags)
    good = 0
    oldest_age = 0.0
    stale_tags: list[str] = []
    for tag in registry.tags:
        item = values.get(tag.id) or {}
        if item.get("q") == "GOOD":
            good += 1
            try:
                ts = datetime.fromisoformat(str(item.get("ts")))
            except (TypeError, ValueError):
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            oldest_age = max(oldest_age, (now - ts).total_seconds())
        else:
            stale_tags.append(tag.id)

    coverage = round(good / total * 100, 1) if total else 0.0
    warnings = list(model.warnings)
    if stale_tags:
        warnings.append(
            f"Нет достоверных данных по {len(stale_tags)} тегам: {', '.join(stale_tags[:5])}"
            + (" и др." if len(stale_tags) > 5 else "")
        )
    warnings.append(
        "Точность двойника не измерена: нет валидированного набора исторических данных. "
        "Значение скрыто намеренно, а не заменено оценкой."
    )

    return {
        "version": twin_version(registry),
        "status": "EXPERIMENTAL",
        "built_at": now.isoformat(),
        "basis": {
            "registry_version": getattr(registry, "version", 1),
            "tags": total,
            "lines": len(registry.lines),
            "orders": len(model.by_kind("order")),
            "snapshot_seq": snapshot["seq"],
        },
        "metrics": {
            "coverage_pct": coverage,
            "tags_good": good,
            "tags_total": total,
            "freshness_sec": round(oldest_age, 2) if good else None,
            "accuracy": None,
        },
        **model.as_dict(),
        "warnings": warnings,
    }
