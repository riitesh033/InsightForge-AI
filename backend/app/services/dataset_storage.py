from pathlib import Path

from app.core.config import settings


def dataset_storage_root() -> Path:
    configured = Path(settings.DATASET_STORAGE_DIR)
    if not configured.is_absolute():
        configured = Path(__file__).resolve().parents[2] / configured
    return configured.resolve()


def resolve_dataset_path(stored_path: str) -> Path:
    path = Path(stored_path)
    if path.is_absolute():
        resolved = path.resolve()
        if resolved.is_file():
            return resolved

        relocated_path = dataset_storage_root() / path.name
        if relocated_path.is_file():
            return relocated_path.resolve()
        return resolved

    legacy_path = (Path.cwd() / path).resolve()
    if legacy_path.is_file():
        return legacy_path

    relocated_path = dataset_storage_root() / path.name
    if relocated_path.is_file():
        return relocated_path.resolve()
    return legacy_path
