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

    def _manifest_path(
        self,
        storage_id: str,
    ) -> str:
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
        """
        Create a short-lived signed upload URL for a
        Supabase Storage object.

        The browser can use the returned token to upload
        directly to Supabase without receiving the
        service-role key.
        """

        self._require_configuration()

        if not storage_id:
            raise ValueError(
                "Storage identifier is required."
            )

        try:
            response = (
                self.client.storage
                .from_(self.bucket)
                .create_signed_upload_url(
                    storage_id,
                    options={
                        "upsert": "false",
                    },
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
                "Failed to create Supabase signed "
                "upload URL: %s",
                exc,
            )
            raise

    def create_signed_chunk_upload_url(
        self,
        storage_id: str,
        chunk_index: int,
    ) -> dict[str, str]:
        """
        Create a short-lived signed upload URL for one
        dataset chunk.

        Each chunk is stored as a separate Supabase
        Storage object.
        """

        self._require_configuration()

        if not storage_id:
            raise ValueError(
                "Storage identifier is required."
            )

        if chunk_index < 0:
            raise ValueError(
                "chunk_index must be non-negative."
            )

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
        Create a manifest for chunks uploaded directly
        from the browser to Supabase Storage.

        The chunk objects are stored at:

            <storage_id>/chunk_000000
            <storage_id>/chunk_000001
            ...

        The manifest is stored at:

            <storage_id>/manifest.json
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

        chunks: list[dict[str, Any]] = []

        for chunk_index in range(total_chunks):
            chunk_path = (
                f"{storage_id}/"
                f"chunk_{chunk_index:06d}"
            )

            chunks.append(
                {
                    "index": chunk_index,
                    "path": chunk_path,
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
                        "content-type": (
                            "application/json"
                        ),
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

    def download_chunks_to_file(
        self,
        storage_id: str,
        output_path: Path,
        total_chunks: int,
    ) -> Path:
        """
        Reconstruct browser-uploaded chunks into a local file.

        Chunks are stored at:

            <storage_id>/chunk_000000
            <storage_id>/chunk_000001
            ...

        The reconstructed file is written to output_path.
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
                exc
            )
            raise

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