"""Экспорт 1C EnterpriseData и OPC UA NodeSet2 (read-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from factoria.auth.rbac import Principal, require
from factoria.exports.enterprise import enterprise_xml
from factoria.exports.nodeset2 import nodeset2_xml

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.get("/1c-enterprise.xml")
async def export_1c(
    request: Request,
    template_id: str | None = Query(default=None),
    principal: Principal = Depends(require("read")),
) -> Response:
    data = enterprise_xml(request.app.state.registry, template_id)
    return Response(content=data, media_type="application/xml; charset=utf-8")


@router.get("/opcua-nodeset2.xml")
async def export_nodeset2(
    request: Request,
    principal: Principal = Depends(require("read")),
) -> Response:
    data = nodeset2_xml(request.app.state.registry)
    return Response(content=data, media_type="application/xml; charset=utf-8")
