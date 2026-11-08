"""Генерация OPC UA NodeSet2 (IEC 62541-6) из реального реестра тегов."""
from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from factoria.tags.registry import Registry

_DATA_TYPES = {
    "bool": "i=1",
    "float": "i=11",  # Double
    "uint16": "i=5",
    "string": "i=12",
}


def nodeset2_xml(registry: Registry) -> bytes:
    root = Element(
        "UANodeSet",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
            "xmlns": "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd",
        },
    )
    uris = SubElement(root, "NamespaceUris")
    SubElement(uris, "Uri").text = registry.namespace

    for tag in registry.tags:
        node_id = f"ns=1;s={tag.id}"
        var = SubElement(
            root,
            "UAVariable",
            {
                "NodeId": node_id,
                "BrowseName": f"1:{tag.name}",
                "DataType": _DATA_TYPES.get(tag.type, "i=24"),
                "AccessLevel": "1",
            },
        )
        SubElement(var, "DisplayName").text = tag.id
        desc = SubElement(var, "Description")
        desc.text = (
            f"line={tag.line}, type={tag.type}, unit={tag.unit or '-'}, "
            f"max_age={tag.max_age_seconds}s, writable={tag.writable}"
        )

    for method in registry.methods:
        for line in registry.lines:
            node_id = f"ns=1;s={line}.{method.name}"
            SubElement(
                root,
                "UAMethod",
                {
                    "NodeId": node_id,
                    "BrowseName": f"1:{method.name}",
                    "Executable": "true",
                    "UserExecutable": "false",
                },
            )
            # informational only; execution remains gated by approvals/A1 in application layer

    return b'<?xml version="1.0" encoding="utf-8"?>\n' + tostring(root, encoding="unicode").encode("utf-8")
