"""Auto-discovers dataset modules at import time."""
from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Iterable

from app.datasets.base import DatasetService

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, DatasetService] = {}


def _is_dataset_dir(path: Path) -> bool:
    return (path / "service.py").exists() and (path / "__init__.py").exists()


def discover() -> dict[str, DatasetService]:
    """Import every dataset package under `app.datasets` and instantiate its service."""
    if _REGISTRY:
        return _REGISTRY

    pkg = importlib.import_module("app.datasets")
    base_dir = Path(pkg.__file__).parent  # type: ignore[arg-type]

    for module_info in pkgutil.iter_modules([str(base_dir)]):
        if not module_info.ispkg:
            continue
        module_dir = base_dir / module_info.name
        if not _is_dataset_dir(module_dir):
            continue

        full_name = f"app.datasets.{module_info.name}.service"
        try:
            module = importlib.import_module(full_name)
        except Exception:  # noqa: BLE001 - log and continue so one bad dataset doesn't kill the API
            logger.exception("Failed to import dataset module %s", full_name)
            continue

        service_cls = getattr(module, "Service", None)
        if service_cls is None or not issubclass(service_cls, DatasetService):
            logger.warning("Dataset %s missing `Service` subclass; skipping", module_info.name)
            continue

        try:
            service = service_cls(module_dir=module_dir)
        except Exception:
            logger.exception("Failed to instantiate dataset %s", module_info.name)
            continue

        _REGISTRY[service.id] = service
        logger.info("Registered dataset '%s' (%s)", service.id, service.name)

    return _REGISTRY


def all_datasets() -> Iterable[DatasetService]:
    return discover().values()


def get(dataset_id: str) -> DatasetService | None:
    return discover().get(dataset_id)
