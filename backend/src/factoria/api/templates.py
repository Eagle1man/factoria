"""Каталог шаблонов цехов (read-only, интеграция спеки Stitch)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from factoria.auth.rbac import Principal, require
from factoria.templates.catalog import get_template, list_templates

router = APIRouter(prefix="/api/v1", tags=["templates"])


@router.get("/templates")
async def templates(principal: Principal = Depends(require("read"))) -> dict:
    items = list_templates()
    return {"templates": items, "count": len(items)}


@router.get("/templates/{template_id}")
async def template_detail(
    template_id: str,
    principal: Principal = Depends(require("read")),
) -> dict:
    item = get_template(template_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="шаблон не найден")
    return item.to_dict()
