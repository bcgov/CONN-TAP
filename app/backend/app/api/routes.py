"""Top-level API router."""
from fastapi import APIRouter

from app.api.endpoints import datasets as datasets_admin
from app.api.endpoints import datasets_api

router = APIRouter()

# Modular dataset/reporting layer (registry-driven).
router.include_router(datasets_api.router, prefix="/datasets", tags=["datasets"])

# Admin CRUD for the `datasets` registry table.
router.include_router(
    datasets_admin.router,
    prefix="/admin/datasets",
    tags=["admin: datasets"],
)
