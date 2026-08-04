import shutil
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.crud.crud_dataset import create_dataset
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.services.insights import (
    calculate_quality_score,
    generate_dataset_summary,
)
from app.services.profiling import profile_dataframe

UPLOAD_DIR = Path("app/uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def make_json_serializable(obj):
    """Recursively convert pandas/numpy objects into JSON-safe values."""

    if isinstance(obj, dict):
        return {
            k: make_json_serializable(v)
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [
            make_json_serializable(v)
            for v in obj
        ]

    if isinstance(obj, tuple):
        return tuple(
            make_json_serializable(v)
            for v in obj
        )

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, pd.Timedelta):
        return str(obj)

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.bool_):
        return bool(obj)

    if pd.isna(obj):
        return None

    return obj


def upload_dataset(
    db: Session,
    file: UploadFile,
    owner_id: int,
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV, XLSX and XLS files are supported.",
        )

    # File size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Maximum upload size is 20 MB.",
        )

    unique_filename = f"{uuid4().hex}{extension}"
    save_path = UPLOAD_DIR / unique_filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if extension == ".csv":
            dataframe = pd.read_csv(save_path)
        else:
            dataframe = pd.read_excel(save_path)

    except Exception:
        save_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail="Unable to read dataset.",
        )

    try:
        analysis_data = profile_dataframe(dataframe)

        # Convert everything into JSON-safe objects
        analysis_data = make_json_serializable(analysis_data)

        analysis_text = generate_dataset_summary(
            analysis_data
        )

        quality_score = calculate_quality_score(
            analysis_data
        )

    except Exception as e:
        save_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Unable to profile dataset. {str(e)}",
        )

    dataset = Dataset(
        filename=unique_filename,
        original_filename=file.filename,
        file_type=extension.replace(".", ""),
        file_size=file_size,
        file_path=str(save_path),
        rows=len(dataframe),
        columns=len(dataframe.columns),
        owner_id=owner_id,
    )

    dataset = create_dataset(
        db=db,
        dataset=dataset,
    )

    analysis = Analysis(
        dataset_id=dataset.id,
        summary=analysis_data["summary"],
        summary_text=analysis_text,
        quality_score=quality_score,
        column_info=analysis_data["column_info"],
        statistics=analysis_data["statistics"],
        missing_values=analysis_data["missing_values"],
        duplicates=analysis_data["duplicates"],
        correlations=analysis_data["correlations"],
        outliers=analysis_data["outliers"],
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return dataset