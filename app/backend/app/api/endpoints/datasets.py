"""Dataset endpoints — example CRUD + pandas-powered summary."""
from io import StringIO

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetCreate, DatasetRead

router = APIRouter()


@router.get("", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    return list(db.scalars(select(Dataset).order_by(Dataset.id.desc())))


@router.post("", response_model=DatasetRead, status_code=201)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> Dataset:
    dataset = Dataset(**payload.model_dump())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/summary/preview")
def summary_preview(db: Session = Depends(get_db)) -> dict:
    """Return a pandas-derived summary of the datasets table."""
    rows = db.execute(select(Dataset.id, Dataset.name, Dataset.source)).all()
    df = pd.DataFrame(rows, columns=["id", "name", "source"])
    return {
        "row_count": int(len(df)),
        "by_source": df.groupby("source").size().to_dict() if not df.empty else {},
        "preview_csv": df.head(10).to_csv(index=False) if not df.empty else "",
    }
