from pathlib import Path, PurePosixPath

from app.core.config import settings
from app.services.cloud_storage import supabase_storage
from app.utils.files import create_temporary_file_path


CLOUD_STORAGE_PREFIX = "supabase:"


def dataset_storage_root() -> Path:
    """
    Return the local dataset storage directory.

    Local storage is still used for temporary processing and
    when cloud storage is disabled.
    """

    storage_setting = settings.DATASET_STORAGE_DIR.strip()

    if not storage_setting:
        raise RuntimeError(
            "DATASET_STORAGE_DIR must not be empty."
        )

    configured = Path(storage_setting)

    if not configured.is_absolute():
        configured = (
            Path(__file__).resolve().parents[2]
            / configured
        )

    return configured.resolve()


def resolve_dataset_path(stored_path: str) -> Path:
    """
    Resolve a legacy/local dataset path safely.

    Cloud-backed datasets must be resolved through
    get_dataset_local_path().
    """

    if not isinstance(stored_path, str):
        raise ValueError(
            "Invalid dataset storage identifier."
        )

    normalized = stored_path.replace("\\", "/")

    if normalized.startswith(CLOUD_STORAGE_PREFIX):
        raise ValueError(
            "Cloud dataset paths must be resolved through "
            "get_dataset_local_path()."
        )

    parts = PurePosixPath(normalized).parts

    if (
        not normalized
        or "\x00" in normalized
        or ".." in parts
    ):
        raise ValueError(
            "Invalid dataset storage identifier."
        )

    filename = PurePosixPath(normalized).name

    if filename in {"", ".", ".."}:
        raise ValueError(
            "Invalid dataset storage identifier."
        )

    root = dataset_storage_root()

    resolved = (root / filename).resolve()

    if not resolved.is_relative_to(root):
        raise ValueError(
            "Invalid dataset storage identifier."
        )

    return resolved


def create_local_dataset_path(filename: str) -> Path:
    """
    Create a safe path for temporarily storing a dataset locally.
    """

    path = resolve_dataset_path(filename)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def build_cloud_storage_id(
    dataset_id: int | str,
) -> str:
    """
    Build the short storage identifier stored in Dataset.file_path.

    Example:
        supabase:datasets/123
    """

    return (
        f"{CLOUD_STORAGE_PREFIX}"
        f"datasets/{dataset_id}"
    )


def get_cloud_storage_id(
    stored_path: str,
) -> str:
    """
    Extract the Supabase storage identifier from Dataset.file_path.

    Example:
        supabase:datasets/123
        ->
        datasets/123
    """

    if not isinstance(stored_path, str):
        raise ValueError(
            "Invalid dataset storage identifier."
        )

    if not stored_path.startswith(
        CLOUD_STORAGE_PREFIX
    ):
        raise ValueError(
            "Dataset is not stored in Supabase."
        )

    storage_id = stored_path[
        len(CLOUD_STORAGE_PREFIX):
    ]

    if not storage_id:
        raise ValueError(
            "Invalid Supabase storage identifier."
        )

    normalized = storage_id.replace("\\", "/")

    parts = PurePosixPath(normalized).parts

    if (
        "\x00" in normalized
        or ".." in parts
        or not normalized.startswith("datasets/")
    ):
        raise ValueError(
            "Invalid Supabase storage identifier."
        )

    return normalized


def is_cloud_dataset(
    stored_path: str,
) -> bool:
    """
    Return True when the dataset is stored in Supabase.
    """

    return (
        isinstance(stored_path, str)
        and stored_path.startswith(
            CLOUD_STORAGE_PREFIX
        )
    )


def get_dataset_local_path(
    stored_path: str,
) -> tuple[Path, bool]:
    """
    Return a local file path for a dataset.

    Returns:
        (path, temporary)

    Local dataset:
        temporary = False

    Supabase dataset:
        dataset is reconstructed into a temporary local file,
        temporary = True.
    """

    if not is_cloud_dataset(stored_path):
        path = resolve_dataset_path(
            stored_path
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Dataset file not found: {path}"
            )

        return path, False

    storage_id = get_cloud_storage_id(
        stored_path
    )

    temporary_path = create_temporary_file_path(
        prefix="insightforge_dataset_",
        suffix=".dataset",
    )

    try:
        downloaded = (
            supabase_storage.download_file(
                storage_id,
                temporary_path,
            )
        )

        return downloaded, True

    except Exception:
        temporary_path.unlink(
            missing_ok=True
        )
        raise


def cleanup_dataset_local_path(
    path: Path,
    temporary: bool,
) -> None:
    """
    Remove a temporary reconstructed dataset.

    Permanent local datasets are never removed here.
    """

    if temporary:
        path.unlink(
            missing_ok=True
        )


def delete_dataset_storage(
    stored_path: str,
) -> None:
    """
    Delete the dataset from Supabase when it is cloud-backed.

    Local datasets are ignored here because their existing
    deletion logic remains responsible for local files.
    """

    if not is_cloud_dataset(stored_path):
        return

    storage_id = get_cloud_storage_id(
        stored_path
    )

    supabase_storage.delete_file(
        storage_id
    )
