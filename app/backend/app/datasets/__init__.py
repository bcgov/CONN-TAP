"""Dataset framework.

Each dataset is a self-contained module under `app/datasets/<dataset_id>/` with:

    queries.sql   -- named SQL queries (`-- name: <key>` blocks), optional
    schema.py     -- pydantic models for filters and rows
    service.py    -- DatasetService subclass exposing `run(filters)`
    config.json   -- metadata: id, name, description, default query, filters, etc.

Datasets are auto-discovered at startup by `app.datasets.registry`.
"""
