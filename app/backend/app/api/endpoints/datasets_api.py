"""Generic, registry-driven dataset endpoints.

Exposes:
    GET  /datasets               -> list registered datasets
    GET  /datasets/{id}          -> dataset metadata (filters, queries, config)
    GET  /datasets/{id}/data     -> execute the dataset with query-string filters
    POST /datasets/{id}/data     -> execute the dataset with a JSON filter body
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.datasets import registry
from app.db.session import get_db

router = APIRouter()


@router.get("")
def list_datasets() -> list[dict[str, Any]]:
    return [d.describe() for d in registry.all_datasets()]


@router.get("/{dataset_id}")
def describe_dataset(dataset_id: str) -> dict[str, Any]:
    service = registry.get(dataset_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset '{dataset_id}'")
    return service.describe()


@router.get("/{dataset_id}/data")
def run_dataset_get(
    dataset_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    service = registry.get(dataset_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset '{dataset_id}'")

    filters: dict[str, Any] = {
        key: request.query_params.getlist(key) if len(request.query_params.getlist(key)) > 1 else request.query_params[key]
        for key in dict.fromkeys(request.query_params.keys())
    }
    try:
        return service.run(db, filters).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{dataset_id}/data")
def run_dataset_post(
    dataset_id: str,
    filters: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    service = registry.get(dataset_id)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset '{dataset_id}'")

    try:
        return service.run(db, filters).to_dict()
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
