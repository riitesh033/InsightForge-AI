from pathlib import Path, PurePosixPath

from app.core.config import settings


def dataset_storage_root() -> Path:
    storage_setting = settings.DATASET_STORAGE_DIR.strip()
    if not storage_setting:
        raise RuntimeError("DATASET_STORAGE_DIR must not be empty.")

    configured = Path(storage_setting)
    if not configured.is_absolute():
        configured = Path(__file__).resolve().parents[2] / configured
    return configured.resolve()


def resolve_dataset_path(stored_path: str) -> Path:
    if not isinstance(stored_path, str):
        raise ValueError("Invalid dataset storage identifier.")

    normalized = str(stored_path).replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    if not normalized or "\x00" in normalized or ".." in parts:
        raise ValueError("Invalid dataset storage identifier.")

    filename = PurePosixPath(normalized).name
    if filename in {"", ".", ".."}:
        raise ValueError("Invalid dataset storage identifier.")

    root = dataset_storage_root()
    resolved = (root / filename).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Invalid dataset storage identifier.")

    return resolved
