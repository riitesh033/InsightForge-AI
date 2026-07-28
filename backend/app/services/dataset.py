import shutil
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.crud.crud_dataset import create_dataset
from app.models.analysis import Analysis
from app.models.dataset import Dataset
from app.services.profiling import profile_dataframe

UPLOAD_DIR = Path("app/uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


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

    # Generate unique filename
    unique_filename = f"{uuid4().hex}{extension}"

    save_path = UPLOAD_DIR / unique_filename

    # Save uploaded file
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Read dataset
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

    # Generate profile
    try:
        analysis_data = profile_dataframe(dataframe)

    except Exception:
        save_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail="Unable to profile dataset.",
        )

    # Save dataset metadata
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

    # Save analysis
    analysis = Analysis(
        dataset_id=dataset.id,
        summary=analysis_data["summary"],
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