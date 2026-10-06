import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger(__name__)


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
        return (
            settings.SUPABASE_CHUNK_SIZE_MB
            * 1024
            * 1024
        )

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

    def _manifest_path(self, storage_id: str) -> str:
        return (
            f"{storage_id}/"
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
        """

        self._require_configuration()

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

            # Best-effort cleanup of chunks created before
            # the failure.
            self._delete_chunk_paths(
                [
                    chunk["path"]
                    for chunk in chunks
                    if chunk.get("path")
                ]
            )

            raise

    def get_manifest(
        self,
        storage_id: str,
    ) -> dict[str, Any]:
        """
        Download and decode the manifest for a dataset.
        """

        self._require_configuration()

        manifest_path = self._manifest_path(
            storage_id
        )

        try:
            data = (
                self.client.storage
                .from_(self.bucket)
                .download(manifest_path)
            )
        except Exception as exc:
            raise FileNotFoundError(
                "Supabase dataset manifest was not found."
            ) from exc

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

    def download_file(
        self,
        manifest: dict[str, Any] | str,
        destination: Path | None = None,
    ) -> Path:
        """
        Reconstruct a Supabase dataset into a local file.

        `manifest` may be either:

        - an already-loaded manifest dictionary, or
        - a Supabase storage identifier.
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
            fd, temporary_path = tempfile.mkstemp(
                prefix="insightforge_dataset_",
                suffix=".dataset",
            )

            os.close(fd)

            destination = Path(
                temporary_path
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
                "Supabase storage manifest contains "
                "no chunks."
            )

        expected_size = manifest.get(
            "original_size"
        )

        try:
            with destination.open("wb") as output:
                for chunk in chunks:
                    object_path = chunk.get(
                        "path"
                    )

                    if not object_path:
                        raise RuntimeError(
                            "Supabase manifest contains "
                            "an invalid chunk path."
                        )

                    data = (
                        self.client.storage
                        .from_(self.bucket)
                        .download(object_path)
                    )

                    output.write(data)

            if (
                expected_size is not None
                and destination.stat().st_size
                != expected_size
            ):
                raise RuntimeError(
                    "Reconstructed dataset size does not "
                    "match the stored file size."
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

    def delete_file(
        self,
        manifest: dict[str, Any] | str,
    ) -> None:
        """
        Delete all chunks and the manifest belonging to a
        Supabase dataset.

        `manifest` may be either a manifest dictionary or
        a storage identifier.
        """

        if not self.is_configured():
            return

        try:
            if isinstance(manifest, str):
                manifest = self.get_manifest(
                    manifest
                )

            if not isinstance(manifest, dict):
                return

            storage_id = manifest.get(
                "storage_id"
            )

            chunks = manifest.get(
                "chunks",
                [],
            )

            paths = [
                chunk["path"]
                for chunk in chunks
                if chunk.get("path")
            ]

            if storage_id:
                paths.append(
                    self._manifest_path(
                        storage_id
                    )
                )

            self._delete_chunk_paths(
                paths
            )

        except Exception:
            logger.exception(
                "Failed to delete Supabase dataset."
            )


supabase_storage = SupabaseStorage()