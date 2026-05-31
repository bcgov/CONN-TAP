"""Pydantic schemas for Dataset."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str
    source: str


class DatasetCreate(DatasetBase):
    pass


class DatasetRead(DatasetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
