import json
import logging
from pathlib import Path
from typing import Any

from supabase import Client, create_client

from app.core.config import settings
from app.utils.files import create_temporary_file_path

logger = logging.getLogger(__name__)

CLOUD_STORAGE_PREFIX = "supabase:"

# Supabase rejects any single object larger than the bucket's configured
# upload limit (50 MiB on the default plan). Chunks are clamped to stay
# safely below it, and never shrink below 1 MiB.
MAX_SUPABASE_OBJECT_BYTES = 50 * 1024 * 1024
MIN_SUPABASE_CHUNK_BYTES = 1024 * 1024


def normalize_storage_id(storage_id: str) -> str:
    """Return the canonical Supabase object prefix for a storage identifier.

    ``datasets.file_path`` stores identifiers such as ``supabase:datasets/12``
    while Supabase object paths are ``datasets/12/...``. Historic revisions
    handed the fully prefixed identifier straight to the storage layer, so
    those objects were written under object paths beginning with ``supabase:``
    and could never be read back, because every reader strips the prefix first.
    Normalising at this boundary keeps writers and readers in agreement.
    """

    if not isinstance(storage_id, str):
        raise ValueError("Storage identifier must be a string.")

    normalized = storage_id.replace("\\", "/").strip().lstrip("/")

    if normalized.startswith(CLOUD_STORAGE_PREFIX):
        normalized = normalized[len(CLOUD_STORAGE_PREFIX):]

    normalized = normalized.strip("/")

    if not normalized:
        raise ValueError("Storage identifier must not be empty.")

    if "\x00" in normalized or ".." in normalized.split("/"):
        raise ValueError("Invalid storage identifier.")

    return normalized


def legacy_storage_id(storage_id: str) -> str:
    """Return the pre-fix (``supabase:``-prefixed) prefix for an identifier."""

    return f"{CLOUD_STORAGE_PREFIX}{normalize_storage_id(storage_id)}"


class SupabaseStorage:
    """
    Supabase Storage wrapper for InsightForge AI.

    Large datasets are split into chunks so that each individual
    Supabase Storage object stays below the configured chunk size.

    A small manifest is stored alongside the chunks. The database
    only needs to store the short storage identifier.
    """

    MANIFEST_FILENAME = "manifest.json"

    def __init__(self) -> None:
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            if not settings.SUPABASE_URL:
                raise RuntimeError(
                    "SUPABASE_URL is not configured."
                )

            if not settings.SUPABASE_SERVICE_ROLE_KEY:
                raise RuntimeError(
                    "SUPABASE_SERVICE_ROLE_KEY is not configured."
                )

            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )

        return self._client

    @property
    def bucket(self) -> str:
        return settings.SUPABASE_BUCKET

    @property
    def chunk_size(self) -> int:
        """Return the chunk size in bytes, safely below Supabase's cap."""

        configured = (
            settings.SUPABASE_CHUNK_SIZE_MB
            * 1024
            * 1024
        )

        if configured > MAX_SUPABASE_OBJECT_BYTES:
            logger.warning(
                "SUPABASE_CHUNK_SIZE_MB=%s exceeds the maximum supported "
                "object size; using %s MiB instead.",
                settings.SUPABASE_CHUNK_SIZE_MB,
                MAX_SUPABASE_OBJECT_BYTES // (1024 * 1024),
            )
            return MAX_SUPABASE_OBJECT_BYTES

        return max(configured, MIN_SUPABASE_CHUNK_BYTES)

    def is_configured(self) -> bool:
        return bool(
            settings.SUPABASE_URL
            and settings.SUPABASE_SERVICE_ROLE_KEY
            and settings.SUPABASE_BUCKET
        )

    def _require_configuration(self) -> None:
        if not self.is_configured():
            raise RuntimeError(
                "Supabase Storage is not configured."
            )

    def _manifest_path(
        self,
        storage_id: str,
    ) -> str:
        return (
            f"{normalize_storage_id(storage_id)}/"
            f"{self.MANIFEST_FILENAME}"
        )

    def upload_file(
        self,
        file_path: Path,
        storage_id: str,
    ) -> dict[str, Any]:
        """
        Upload a local file to Supabase Storage.

        The file is split into chunks. A manifest containing the
        chunk information is then stored separately.

        ``storage_id`` may be supplied with or without the
        ``supabase:`` prefix; only the canonical object prefix is used.
        """

        self._require_configuration()

        storage_id = normalize_storage_id(storage_id)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        file_size = file_path.stat().st_size

        chunk_count = max(
            1,
            (
                file_size
                + self.chunk_size
                - 1
            )
            // self.chunk_size,
        )

        chunks: list[dict[str, Any]] = []

        try:
            with file_path.open("rb") as source:
                for chunk_index in range(chunk_count):
                    chunk = source.read(
                        self.chunk_size
                    )

                    if not chunk:
                        break

                    object_path = (
                        f"{storage_id}/"
                        f"chunk_{chunk_index:06d}"
                    )

                    (
                        self.client.storage
                        .from_(self.bucket)
                        .upload(
                            object_path,
                            chunk,
                            {
                                "content-type": (
                                    "application/"
                                    "octet-stream"
                                ),
                                "upsert": "true",
                            },
                        )
                    )

                    chunks.append(
                        {
                            "index": chunk_index,
                            "path": object_path,
                            "size": len(chunk),
                        }
                    )

            manifest = {
                "storage": "supabase",
                "storage_id": storage_id,
                "original_size": file_size,
                "chunk_size": self.chunk_size,
                "chunk_count": len(chunks),
                "chunks": chunks,
            }

            manifest_bytes = json.dumps(
                manifest,
                separators=(",", ":"),
            ).encode("utf-8")

            manifest_path = self._manifest_path(
                storage_id
            )

            (
                self.client.storage
                .from_(self.bucket)
                .upload(
                    manifest_path,
                    manifest_bytes,
                    {
                        "content-type": (
                            "application/json"
                        ),
                        "upsert": "true",
                    },
                )
            )

            return manifest

        except Exception:
            logger.exception(
                "Failed to upload dataset to Supabase."
            )

            self._delete_chunk_paths(
                [
                    chunk["path"]
                    for chunk in chunks
                    if chunk.get("path")
                ]
            )

            raise

    def create_signed_upload_url(
        self,
        storage_id: str,
    ) -> dict[str, str]:
        """Create a short-lived signed upload URL for a Supabase object."""

        self._require_configuration()

        storage_id = normalize_storage_id(storage_id)

        try:
            response = (
                self.client.storage
                .from_(self.bucket)
                .create_signed_upload_url(
                    storage_id,
                    options={"upsert": "false"},
                )
            )

            if not isinstance(response, dict):
                raise RuntimeError(
                    "Supabase returned an invalid signed "
                    "upload response."
                )

            token = response.get("token")

            if not token:
                raise RuntimeError(
                    "Supabase did not return a signed "
                    "upload token."
                )

            return {
                "path": storage_id,
                "token": token,
            }

        except Exception as exc:
            logger.exception(
                "Failed to create Supabase signed upload URL: %s",
                exc,
            )
            raise

    def create_signed_chunk_upload_url(
        self,
        storage_id: str,
        chunk_index: int,
    ) -> dict[str, str]:
        """Create a short-lived signed upload URL for one dataset chunk."""

        self._require_configuration()

        if not storage_id:
            raise ValueError(
                "Storage identifier is required."
            )

        if chunk_index < 0:
            raise ValueError(
                "chunk_index must be non-negative."
            )

        storage_id = normalize_storage_id(storage_id)

        chunk_path = (
            f"{storage_id}/"
            f"chunk_{chunk_index:06d}"
        )

        try:
            response = (
                self.client.storage
                .from_(self.bucket)
                .create_signed_upload_url(
                    chunk_path,
                )
            )

            if not isinstance(response, dict):
                raise RuntimeError(
                    "Supabase returned an invalid signed "
                    "chunk upload response."
                )

            token = response.get("token")

            if not token:
                raise RuntimeError(
                    "Supabase did not return a signed "
                    "chunk upload token."
                )

            return {
                "path": chunk_path,
                "token": token,
            }

        except Exception as exc:
            logger.exception(
                "Failed to create Supabase signed "
                "chunk upload URL: %s",
                exc,
            )
            raise

    def create_chunk_manifest(
        self,
        storage_id: str,
        total_chunks: int,
        file_size: int,
    ) -> dict[str, Any]:
        """
        Create a manifest for chunks uploaded directly from the browser.

        Chunk objects live at ``<storage_id>/chunk_000000`` and the
        manifest at ``<storage_id>/manifest.json``.
        """

        self._require_configuration()

        if not storage_id:
            raise ValueError(
                "Storage identifier is required."
            )

        if total_chunks <= 0:
            raise ValueError(
                "total_chunks must be greater than zero."
            )

        if file_size <= 0:
            raise ValueError(
                "file_size must be greater than zero."
            )

        storage_id = normalize_storage_id(storage_id)

        chunks: list[dict[str, Any]] = []

        for chunk_index in range(total_chunks):
            chunks.append(
                {
                    "index": chunk_index,
                    "path": (
                        f"{storage_id}/"
                        f"chunk_{chunk_index:06d}"
                    ),
                }
            )

        manifest = {
            "storage": "supabase",
            "storage_id": storage_id,
            "original_size": file_size,
            "chunk_size": self.chunk_size,
            "chunk_count": total_chunks,
            "chunks": chunks,
        }

        manifest_path = self._manifest_path(
            storage_id
        )

        try:
            manifest_bytes = json.dumps(
                manifest,
                separators=(",", ":"),
            ).encode("utf-8")

            (
                self.client.storage
                .from_(self.bucket)
                .upload(
                    manifest_path,
                    manifest_bytes,
                    {
                        "content-type": "application/json",
                        "upsert": "true",
                    },
                )
            )

            return manifest

        except Exception as exc:
            logger.exception(
                "Failed to create Supabase chunk manifest: %s",
                exc,
            )
            raise

    def get_manifest(
        self,
        storage_id: str,
    ) -> dict[str, Any]:
        """
        Download and decode the manifest for a dataset.

        Datasets written before the storage-path fix live under a
        ``supabase:``-prefixed object path, so both spellings are tried
        until one resolves.
        """

        self._require_configuration()

        data = None

        for candidate in (
            self._manifest_path(storage_id),
            f"{legacy_storage_id(storage_id)}/"
            f"{self.MANIFEST_FILENAME}",
        ):
            try:
                data = (
                    self.client.storage
                    .from_(self.bucket)
                    .download(candidate)
                )
                break
            except Exception:
                data = None

        if data is None:
            raise FileNotFoundError(
                "Supabase dataset manifest was not found."
            )

        try:
            manifest = json.loads(
                data.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise RuntimeError(
                "Supabase dataset manifest is invalid."
            ) from exc

        if not isinstance(manifest, dict):
            raise RuntimeError(
                "Supabase dataset manifest has an invalid format."
            )

        if manifest.get("storage") != "supabase":
            raise RuntimeError(
                "Supabase dataset manifest has an invalid storage type."
            )

        return manifest

    def download_chunks_to_file(
        self,
        storage_id: str,
        output_path: Path,
        total_chunks: int,
    ) -> Path:
        """Reconstruct browser-uploaded chunks into a local file."""

        self._require_configuration()

        if not storage_id:
            raise ValueError(
                "Storage identifier is required."
            )

        if total_chunks <= 0:
            raise ValueError(
                "total_chunks must be greater than zero."
            )

        storage_id = normalize_storage_id(storage_id)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            with output_path.open("wb") as output_file:
                for chunk_index in range(total_chunks):
                    chunk_path = (
                        f"{storage_id}/"
                        f"chunk_{chunk_index:06d}"
                    )

                    response = (
                        self.client.storage
                        .from_(self.bucket)
                        .download(chunk_path)
                    )

                    if not response:
                        raise FileNotFoundError(
                            f"Dataset chunk {chunk_index} "
                            "was not found."
                        )

                    output_file.write(response)

            return output_path

        except Exception as exc:
            output_path.unlink(
                missing_ok=True
            )

            logger.exception(
                "Failed to reconstruct Supabase dataset chunks: %s",
                exc,
            )
            raise

    def download_file(
        self,
        manifest: dict[str, Any] | str,
        destination: Path | None = None,
    ) -> Path:
        """
        Reconstruct a Supabase dataset into a local file.

        `manifest` may be an already-loaded manifest dictionary or a
        Supabase storage identifier.
        """

        self._require_configuration()

        if isinstance(manifest, str):
            manifest = self.get_manifest(
                manifest
            )

        if not isinstance(manifest, dict):
            raise ValueError(
                "Invalid Supabase storage manifest."
            )

        if destination is None:
            destination = create_temporary_file_path(
                prefix="insightforge_dataset_",
                suffix=".dataset",
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        chunks = sorted(
            manifest.get("chunks", []),
            key=lambda item: item["index"],
        )

        if not chunks:
            raise RuntimeError(
                "Supabase storage manifest contains no chunks."
            )

        expected_size = manifest.get(
            "original_size"
        )

        try:
            with destination.open("wb") as output:
                for chunk in chunks:
                    object_path = chunk.get("path")

                    if not object_path:
                        raise RuntimeError(
                            "Supabase manifest contains an "
                            "invalid chunk path."
                        )

                    data = (
                        self.client.storage
                        .from_(self.bucket)
                        .download(object_path)
                    )

                    output.write(data)

            if (
                expected_size is not None
                and destination.stat().st_size != expected_size
            ):
                raise RuntimeError(
                    "Reconstructed dataset size does not match "
                    "the stored file size."
                )

            return destination

        except Exception:
            destination.unlink(
                missing_ok=True
            )
            raise

    def _delete_chunk_paths(
        self,
        paths: list[str],
    ) -> None:
        if not paths:
            return

        try:
            (
                self.client.storage
                .from_(self.bucket)
                .remove(paths)
            )
        except Exception:
            logger.exception(
                "Failed to delete Supabase dataset chunks."
            )

    def _list_object_paths(
        self,
        prefix: str,
    ) -> list[str]:
        """Return every object path stored directly under ``prefix``."""

        try:
            entries = (
                self.client.storage
                .from_(self.bucket)
                .list(prefix)
            )
        except Exception:
            logger.warning(
                "Unable to list Supabase objects under %s.",
                prefix,
            )
            return []

        paths: list[str] = []

        for entry in entries or []:
            if isinstance(entry, dict):
                name = entry.get("name")
            else:
                name = getattr(entry, "name", None)

            if isinstance(name, str) and name:
                paths.append(f"{prefix}/{name}")

        return paths

    def delete_file(
        self,
        manifest: dict[str, Any] | str,
    ) -> None:
        """
        Delete every chunk and the manifest belonging to a Supabase dataset.

        Both the canonical and the legacy (``supabase:``-prefixed) object
        prefixes are enumerated, so objects orphaned by the storage-path
        fix are still removed.
        """

        if not self.is_configured():
            return

        try:
            if isinstance(manifest, str):
                try:
                    manifest = self.get_manifest(
                        manifest
                    )
                except (
                    FileNotFoundError,
                    RuntimeError,
                    ValueError,
                ):
                    manifest = {
                        "storage_id": manifest,
                        "chunks": [],
                    }

            if not isinstance(manifest, dict):
                return

            storage_id = manifest.get("storage_id")

            paths = [
                chunk["path"]
                for chunk in manifest.get("chunks", [])
                if chunk.get("path")
            ]

            prefixes: list[str] = []

            if storage_id:
                prefixes.append(
                    normalize_storage_id(storage_id)
                )
                prefixes.append(
                    legacy_storage_id(storage_id)
                )
            else:
                for chunk_path in paths:
                    prefix = chunk_path.rsplit("/", 1)[0]

                    if prefix and prefix not in prefixes:
                        prefixes.append(prefix)

            for prefix in prefixes:
                normalized_prefix = prefix.strip("/")

                if not normalized_prefix:
                    continue

                paths.extend(
                    self._list_object_paths(
                        normalized_prefix
                    )
                )

                paths.append(
                    f"{normalized_prefix}/"
                    f"{self.MANIFEST_FILENAME}"
                )

            self._delete_chunk_paths(
                list(dict.fromkeys(paths))
            )

        except Exception:
            logger.exception(
                "Failed to delete Supabase dataset."
            )


supabase_storage = SupabaseStorage()
