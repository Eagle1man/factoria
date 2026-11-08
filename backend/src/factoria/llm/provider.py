"""Статус/проверка доступности LLM-провайдера.

Секреты (ключи) никогда не возвращаются и не логируются этим модулем.
"""
from __future__ import annotations

from typing import Any

import httpx

from factoria.config import Settings


def _base(provider: str, model: str | None, configured: bool) -> dict[str, Any]:
    return {
        "provider": provider,
        "configured": configured,
        "reachable": False,
        "model": model,
    }


async def llm_status(settings: Settings) -> dict[str, Any]:
    provider = settings.llm_provider
    timeout = settings.llm_timeout_s

    if provider == "none":
        return {**_base("none", None, False), "reachable": False, "detail": "disabled"}

    if provider == "deepseek":
        configured = bool(settings.deepseek_api_key) and settings.allow_external_api
        status = _base("deepseek", settings.deepseek_base_url.split("/")[-1] or "deepseek", configured)
        if not settings.allow_external_api:
            status["detail"] = "external_api_disabled"
            return status
        if not settings.deepseek_api_key:
            status["detail"] = "missing_api_key"
            return status
        # Лёгкая проверка доступности (не раскрывает ключ в ответе).
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Запрос без обязательной передачи ключа в probe; 401/200/404 всё равно = сеть достижима.
                res = await client.get(settings.deepseek_base_url.rstrip("/"))
                status["reachable"] = res.status_code < 500
                status["detail"] = "ok" if status["reachable"] else f"http_{res.status_code}"
        except Exception:
            status["detail"] = "unreachable"
        return status

    if provider == "ollama":
        status = _base("ollama", settings.ollama_model, True)
        url = settings.ollama_url.rstrip("/") + "/api/tags"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(url)
                if res.status_code < 500:
                    status["reachable"] = True
                    status["detail"] = "ok"
                    # Наличие модели — подсказка, не секрет.
                    try:
                        data = res.json()
                        names = [m.get("name", "") for m in data.get("models", []) if isinstance(m, dict)]
                        status["model_present"] = settings.ollama_model in names or any(
                            settings.ollama_model.split(":")[0] in n for n in names
                        )
                    except Exception:
                        status["model_present"] = None
                else:
                    status["detail"] = f"http_{res.status_code}"
        except Exception:
            status["detail"] = "unreachable"
        return status

    return {**_base(provider, None, False), "detail": "unknown_provider"}
