"""Concise, opt-in development traces for the local chat pipeline."""
from __future__ import annotations

import json
import logging
import sys
from typing import Any


_LOGGER = logging.getLogger("omniagent.development")
_LOGGER.propagate = False
_ENABLED = False


def configure_development_logging(enabled: bool) -> None:
    """Configure a dedicated INFO sink that is not filtered by Uvicorn."""
    global _ENABLED
    _ENABLED = bool(enabled)

    if not any(getattr(handler, "_omniagent_dev", False) for handler in _LOGGER.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler._omniagent_dev = True  # type: ignore[attr-defined]
        _LOGGER.addHandler(handler)

    _LOGGER.setLevel(logging.INFO if _ENABLED else logging.WARNING)


def development_trace(section: str, **fields: Any) -> None:
    """Emit allow-listed operational fields; never accepts message or prompt text."""
    if not _ENABLED:
        return

    lines = [f"[{section}]"]
    for key, value in fields.items():
        if key == "top_chunks":
            rendered = json.dumps(value or [], ensure_ascii=False, indent=2)
            lines.append(f"{key}={rendered}")
        else:
            rendered = "null" if value is None else str(value)
            lines.append(f"{key}={rendered}")
    _LOGGER.info("\n".join(lines))
