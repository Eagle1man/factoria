"""Семантическая модель: сущности и связи, выводимые из реестра и заказов."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class Entity:
    id: str
    kind: str
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "name": self.name, "attributes": self.attributes}


@dataclass(frozen=True)
class Relation:
    source: str
    target: str
    kind: str

    def as_dict(self) -> dict[str, str]:
        return {"from": self.source, "to": self.target, "type": self.kind}


@dataclass
class SemanticModel:
    entities: list[Entity]
    relations: list[Relation]
    warnings: list[str]

    def by_kind(self, kind: str) -> list[Entity]:
        return [entity for entity in self.entities if entity.kind == kind]

    def as_dict(self) -> dict[str, Any]:
        return {
            "entities": [entity.as_dict() for entity in self.entities],
            "relations": [relation.as_dict() for relation in self.relations],
            "warnings": list(self.warnings),
        }


def build_semantic(registry, orders: Iterable[Any]) -> SemanticModel:
    entities: list[Entity] = [
        Entity(
            id="enterprise",
            kind="enterprise",
            name="Производственный контур",
            attributes={"lines": len(registry.lines), "tags": len(registry.tags)},
        )
    ]
    relations: list[Relation] = []
    warnings: list[str] = []

    for line in registry.lines:
        tags = registry.line_tags(line)
        entities.append(
            Entity(
                id=line,
                kind="line",
                name=line,
                attributes={
                    "tags": len(tags),
                    "speed_max": registry.thresholds.get("speed_max"),
                    "recipes": list(registry.recipes),
                },
            )
        )
        relations.append(Relation("enterprise", line, "contains"))
        for tag in tags:
            entities.append(
                Entity(
                    id=tag.id,
                    kind="tag",
                    name=tag.name,
                    attributes={
                        "line": line,
                        "unit": tag.unit,
                        "min": tag.min,
                        "max": tag.max,
                        "max_age_seconds": tag.max_age_seconds,
                    },
                )
            )
            relations.append(Relation(line, tag.id, "has_signal"))

    specs: set[str] = set()
    for order in orders:
        entities.append(
            Entity(
                id=order.order_id,
                kind="order",
                name=order.product,
                attributes={
                    "qty": order.qty,
                    "priority": order.priority,
                    "due_date": order.due_date,
                    "spec_id": order.spec_id,
                },
            )
        )
        relations.append(Relation(order.order_id, order.spec_id, "requires_spec"))
        if order.spec_id not in specs:
            specs.add(order.spec_id)
            entities.append(
                Entity(id=order.spec_id, kind="spec", name=order.spec_id, attributes={})
            )

    if specs:
        warnings.append(
            "Заказы из stub не связаны с линиями: в источнике нет поля «линия». "
            "Связь появится с HTTP-сервисами 1С (этап 4b)."
        )
    if not list(orders):
        warnings.append("Заказы не загружены: связь «заказ → спецификация» не построена.")

    return SemanticModel(entities=entities, relations=relations, warnings=warnings)
