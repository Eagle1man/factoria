"""Генерация 1C:EnterpriseData v1.14 (read-only экспорт, без PUSH в контур)."""
from __future__ import annotations

from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring

from factoria.tags.registry import Registry
from factoria.templates.catalog import get_template


def enterprise_xml(registry: Registry, template_id: str | None = None) -> bytes:
    tpl = get_template(template_id) if template_id else None
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M:%S")
    root = Element(
        "EnterpriseData",
        {
            "xmlns": "http://v8.1c.ru/edi/edi_stnd/EnterpriseData/1.14",
            "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
            "formatVersion": "1.14",
        },
    )
    header = SubElement(root, "Header")
    SubElement(header, "FormatVersion").text = "1.14"
    SubElement(header, "CreationDateTime").text = now
    SubElement(header, "SourceApplication").text = "FACTORIA & AI (read-only export)"

    body = SubElement(root, "Body")
    doc = SubElement(body, "Document.СменноСуточноеЗадание")
    SubElement(doc, "Номер").text = (tpl.order_number if tpl else "#FACTORIA-DEMO")
    SubElement(doc, "Дата").text = datetime.now(timezone.utc).date().isoformat()
    SubElement(doc, "Подразделение").text = (
        f"Линии {', '.join(registry.lines)} ({tpl.name})" if tpl else f"Линии {', '.join(registry.lines)}"
    )
    SubElement(doc, "Номенклатура").text = tpl.part_name if tpl else "Демо-изделие"
    SubElement(doc, "План").text = str(tpl.plan_quantity if tpl else 0)
    SubElement(doc, "Факт").text = str(tpl.fact_quantity if tpl else 0)
    SubElement(doc, "Брак").text = str(tpl.defects if tpl else 0)
    SubElement(doc, "Статус").text = "Выгружено_ТолькоЧтение"
    SubElement(doc, "Примечание").text = (
        "Экспорт сформирован из реестра FACTORIA. Отправка в 1C (PUSH/OData) отключена: контур 1C — read-only."
    )

    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode").encode("utf-8")
