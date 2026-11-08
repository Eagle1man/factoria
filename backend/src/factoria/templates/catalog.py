"""Шаблоны производственных линий для демо/витрины.

Данные адаптированы из `docs/spec/stitch-threejs/templates_data.json`.
Привязка к реестру тегов проекта (L1-L3, `registry.yaml`) — явная:
шаблон описывает *вид* цеха, фактические сигналы берутся из OPC UA
через существующие линии. 1C/транспорт — только чтение/экспорт.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    type: str
    status: str
    takt_s: float | None = None
    # линия реестра, к которой логически привязан узел (для живых данных)
    line_id: str | None = None
    metric_label: str | None = None
    metric_value: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Template:
    id: str
    name: str
    description: str
    target_output: str
    takt_time_s: float
    bottleneck_node_id: str
    bottleneck_reason: str
    bottleneck_line_id: str | None
    order_number: str
    part_name: str
    plan_quantity: int
    fact_quantity: int
    defects: int
    stations: tuple[Station, ...] = field(default_factory=tuple)
    # сценарий симулятора, наиболее близкий по смыслу (см. sim.scenarios)
    sim_scenario: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stations"] = [asdict(s) for s in self.stations]
        return data


TEMPLATES: dict[str, Template] = {
    "cnc_metal": Template(
        id="cnc_metal",
        name="ЧПУ металлообработка (DMU 50)",
        description="Лазерная резка, перенос, фрезерование, робот, AGV. Узкое место — шпиндель DMU 50.",
        target_output="1 489 шт/сутки",
        takt_time_s=85.0,
        bottleneck_node_id="ST-03",
        bottleneck_reason="Черновой шпиндель DMU 50 (такт 85 с/деталь) сдерживает подачу.",
        bottleneck_line_id="L1",
        order_number="#1489-M",
        part_name="ВТУЛКА-45М (сталь 40Х)",
        plan_quantity=500,
        fact_quantity=342,
        defects=1,
        sim_scenario="nominal",
        stations=(
            Station("ST-01", "TRUMPF TruLaser 5030 Fiber", "laser", "RUNNING", 24.0, "L1", "Мощность", "4.0 кВт"),
            Station("ST-02", "Конвейерный накопитель", "conveyor", "WARN_QUEUE", None, "L1", "Очередь", "расчётная", "Очередь — расчётный показатель витрины."),
            Station("ST-03", "Siemens Sinumerik DMU 50", "cnc", "BOTTLENECK", 85.0, "L1", "Обороты PV", "из OPC UA", "Живые Speed/Temp/Load — из L1."),
            Station("ST-04", "FANUC M-20iD", "robot", "RUNNING", 14.2, "L2", "Цикл", "14.2 с"),
            Station("ST-05", "AGV-флот", "agv", "STANDBY", None, "L3", "Статус", "ожидание"),
        ),
    ),
    "drone_assembly": Template(
        id="drone_assembly",
        name="Сборка БПЛА и дронов (Fanuc M-20)",
        description="Сборочная линия БПЛА. Узкое место — монтаж электроники роботом.",
        target_output="528 дронов/сутки",
        takt_time_s=42.0,
        bottleneck_node_id="ST-04",
        bottleneck_reason="Монтаж бортовой электроники и автопилота роботом Fanuc (42 с).",
        bottleneck_line_id="L2",
        order_number="#8902-DR",
        part_name="ДРОН-РАЗВЕДЧИК X4-PRO",
        plan_quantity=200,
        fact_quantity=84,
        defects=0,
        sim_scenario="nominal",
        stations=(
            Station("ST-01", "Подача компонентов", "feeder", "RUNNING", 18.0, "L1"),
            Station("ST-02", "Сборка рамы", "assembly", "RUNNING", 30.0, "L1"),
            Station("ST-03", "Пайка/кабель", "process", "RUNNING", 35.0, "L2"),
            Station("ST-04", "FANUC M-20: электроника", "robot", "BOTTLENECK", 42.0, "L2", "Узел", "узкое место"),
            Station("ST-05", "Финальный контроль", "qc", "RUNNING", 20.0, "L3"),
        ),
    ),
    "cubesat_satellite": Template(
        id="cubesat_satellite",
        name="Спутники CubeSat (AeroLab QC)",
        description="Лабораторная сборка CubeSat. Узкое место — термовакуумные испытания.",
        target_output="4 спутника/сутки",
        takt_time_s=12600.0,
        bottleneck_node_id="ST-06",
        bottleneck_reason="Термовакуумное тестирование узлов СЭП и радиоканала (210 мин).",
        bottleneck_line_id="L3",
        order_number="#004-SAT",
        part_name="CUBESAT 6U KOSMOS-IOT",
        plan_quantity=4,
        fact_quantity=1,
        defects=0,
        sim_scenario="hot_start",
        stations=(
            Station("ST-01", "Сборка шасси", "assembly", "RUNNING", 3600.0, "L1"),
            Station("ST-02", "Интеграция полезной нагрузки", "assembly", "RUNNING", 5400.0, "L1"),
            Station("ST-03", "Проверка питания", "test", "RUNNING", 1800.0, "L2"),
            Station("ST-04", "Радиоканал", "test", "RUNNING", 2400.0, "L2"),
            Station("ST-05", "Вибростенд", "test", "RUNNING", 3600.0, "L3"),
            Station("ST-06", "Термовакуумная камера", "chamber", "BOTTLENECK", 12600.0, "L3", "Режим", "длительный прогон"),
        ),
    ),
    "battery_gigafactory": Template(
        id="battery_gigafactory",
        name="Гигафабрика аккумуляторных ячеек",
        description="Линия LFP-ячеек. Узкое место — заполнение электролитом в сухой комнате.",
        target_output="124 282 ячейки/сутки",
        takt_time_s=0.7,
        bottleneck_node_id="ST-05",
        bottleneck_reason="Заполнение электролитом в сухой комнате (такт ограничен выдержкой).",
        bottleneck_line_id="L2",
        order_number="#7710-BAT",
        part_name="LFP-4680",
        plan_quantity=100000,
        fact_quantity=68420,
        defects=142,
        sim_scenario="overload",
        stations=(
            Station("ST-01", "Намотка/укладка", "process", "RUNNING", 0.5, "L1"),
            Station("ST-02", "Сборка корпуса", "assembly", "RUNNING", 0.55, "L1"),
            Station("ST-03", "Сушка", "process", "RUNNING", 0.6, "L2"),
            Station("ST-04", "Вакуумирование", "process", "RUNNING", 0.65, "L2"),
            Station("ST-05", "Заполнение электролитом", "dry_room", "BOTTLENECK", 0.7, "L2", "Узел", "узкое место"),
            Station("ST-06", "Формирование/тест", "test", "RUNNING", 0.6, "L3"),
        ),
    ),
}


def list_templates() -> list[dict[str, Any]]:
    return [t.to_dict() for t in TEMPLATES.values()]


def get_template(template_id: str) -> Template | None:
    return TEMPLATES.get(template_id)
