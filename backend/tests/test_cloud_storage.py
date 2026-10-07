"""Regression tests for Supabase-backed dataset storage.

These tests never touch a live Supabase project. They install an in-memory
stand-in for the Supabase Storage API so the exact object paths the service
reads and writes can be asserted.
"""

import re
from pathlib import Path

import pytest

from app.core.config import settings
from app.services import cloud_storage as cloud_storage_module
from app.services.cloud_storage import (
    MAX_SUPABASE_OBJECT_BYTES,
    SupabaseStorage,
    legacy_storage_id,
    normalize_storage_id,
)

TEST_BUCKET = "test-bucket"


class FakeStorageBucket:
    """Minimal stand-in for ``supabase.storage.from_(bucket)``."""

    def __init__(self, backend: "FakeStorageBackend", name: str) -> None:
        self._backend = backend
        self._name = name

    def upload(self, path, file, file_options=None):
        if isinstance(file, (bytes, bytearray)):
            data = bytes(file)
        elif hasattr(file, "read"):
            data = file.read()
        else:
            data = Path(file).read_bytes()

        self._backend.objects[(self._name, path)] = data

        return {"path": path, "id": path}

    def download(self, path):
        key = (self._name, path)

        if key not in self._backend.objects:
            raise FakeStorageError(f"Object not found: {path}")

        return self._backend.objects[key]

    def remove(self, paths):
        removed = []

        for path in paths:
            if self._backend.objects.pop((self._name, path), None) is not None:
                removed.append(path)

        return removed

    def list(self, prefix):
        entries = {}

        for (bucket, path) in self._backend.objects:
            if bucket != self._name:
                continue

            if not path.startswith(f"{prefix}/"):
                continue

            remainder = path[len(prefix) + 1:]

            if "/" in remainder:
                continue

            entries[remainder] = {"name": remainder}

        return sorted(entries.values(), key=lambda entry: entry["name"])

    def create_signed_upload_url(self, path, options=None):
        return {"token": f"token::{path}", "path": path}


class FakeStorageError(Exception):
    """Raised by the stand-in bucket when an object is missing."""


class FakeStorageBackend:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    def paths(self, name: str = TEST_BUCKET) -> set[str]:
        return {
            path
            for (bucket, path) in self.objects
            if bucket == name
        }


class FakeStorageClient:
    def __init__(self, backend: FakeStorageBackend) -> None:
        self._backend = backend
        self.storage = self

    def from_(self, bucket_name: str) -> FakeStorageBucket:
        return FakeStorageBucket(self._backend, bucket_name)


@pytest.fixture()
def fake_backend() -> FakeStorageBackend:
    return FakeStorageBackend()


@pytest.fixture()
def cloud_storage(monkeypatch, fake_backend) -> SupabaseStorage:
    """Patch the shared storage singleton onto the in-memory backend."""

    monkeypatch.setattr(settings, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setattr(settings, "SUPABASE_BUCKET", TEST_BUCKET)

    shared = cloud_storage_module.supabase_storage
    monkeypatch.setattr(
        shared,
        "_client",
        FakeStorageClient(fake_backend),
    )

    return shared


# ---------------------------------------------------------------------------
# Identifier normalisation
# ---------------------------------------------------------------------------


def test_normalize_storage_id_strips_prefix_and_separators():
    assert normalize_storage_id("supabase:datasets/12") == "datasets/12"
    assert normalize_storage_id("datasets/12") == "datasets/12"
    assert normalize_storage_id("/datasets/12/") == "datasets/12"
    assert normalize_storage_id("datasets\\12") == "datasets/12"


def test_normalize_storage_id_rejects_empty_and_traversal_values():
    for invalid in ("", "supabase:", "/", "datasets/../secrets", "a\x00b"):
        with pytest.raises(ValueError):
            normalize_storage_id(invalid)


def test_legacy_storage_id_round_trips_to_the_prefixed_prefix():
    assert legacy_storage_id("supabase:datasets/4") == "supabase:datasets/4"
    assert legacy_storage_id("datasets/4") == "supabase:datasets/4"


# ---------------------------------------------------------------------------
# Write/read agreement (the original production bug)
# ---------------------------------------------------------------------------


def test_upload_with_prefixed_id_is_readable_by_unprefixed_id(
    cloud_storage, fake_backend, tmp_path
):
    payload = b"id,value\n1,10\n2,20\n"
    source = tmp_path / "dataset.csv"
    source.write_bytes(payload)

    # The upload service historically passed "supabase:datasets/uploads/x".
    cloud_storage.upload_file(source, "supabase:datasets/uploads/abc")

    # No object may be stored under a path beginning with "supabase:".
    assert all(
        not path.startswith("supabase:")
        for path in fake_backend.paths()
    )

    manifest = cloud_storage.get_manifest("datasets/uploads/abc")

    assert manifest["storage_id"] == "datasets/uploads/abc"
    assert manifest["original_size"] == len(payload)
    assert manifest["chunk_count"] == 1

    # Reading through the prefixed form resolves to the same manifest.
    assert cloud_storage.get_manifest(
        "supabase:datasets/uploads/abc"
    )["storage_id"] == "datasets/uploads/abc"


def test_download_file_reconstructs_the_uploaded_bytes(
    cloud_storage, tmp_path
):
    payload = bytes(range(256)) * 40
    source = tmp_path / "dataset.csv"
    source.write_bytes(payload)

    cloud_storage.upload_file(source, "datasets/uploads/roundtrip")

    destination = tmp_path / "restored.csv"

    cloud_storage.download_file(
        "datasets/uploads/roundtrip",
        destination,
    )

    assert destination.read_bytes() == payload


def test_download_file_rejects_size_mismatch(
    cloud_storage, fake_backend, tmp_path
):
    source = tmp_path / "dataset.csv"
    source.write_bytes(b"a,b\n1,2\n")

    cloud_storage.upload_file(source, "datasets/uploads/short")

    # Corrupt the reconstructed size by truncating the stored chunk.
    fake_backend.objects[
        (TEST_BUCKET, "datasets/uploads/short/chunk_000000")
    ] = b"a,b"

    destination = tmp_path / "restored.csv"

    with pytest.raises(RuntimeError, match="size does not match"):
        cloud_storage.download_file(
            "datasets/uploads/short",
            destination,
        )

    assert not destination.exists()


def test_get_manifest_falls_back_to_legacy_prefixed_objects(
    cloud_storage, fake_backend
):
    """Datasets uploaded before the fix still resolve."""

    fake_backend.objects[
        (TEST_BUCKET, "supabase:datasets/legacy/manifest.json")
    ] = (
        b'{"storage":"supabase","storage_id":"supabase:datasets/legacy",'
        b'"original_size":4,"chunk_size":1,'
        b'"chunk_count":1,'
        b'"chunks":[{"index":0,'
        b'"path":"supabase:datasets/legacy/chunk_000000"}]}'
    )

    fake_backend.objects[
        (TEST_BUCKET, "supabase:datasets/legacy/chunk_000000")
    ] = b"data"

    manifest = cloud_storage.get_manifest("datasets/legacy")

    assert manifest["storage_id"] == "supabase:datasets/legacy"

    restored = cloud_storage.download_file("datasets/legacy")

    try:
        assert restored.read_bytes() == b"data"
    finally:
        restored.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Deletion and chunk sizing
# ---------------------------------------------------------------------------


def test_delete_file_removes_canonical_and_legacy_objects(
    cloud_storage, fake_backend, tmp_path
):
    source = tmp_path / "dataset.csv"
    source.write_bytes(b"a,b\n1,2\n")

    cloud_storage.upload_file(
        source,
        "datasets/uploads/purge",
    )

    cloud_storage.upload_file(
        source,
        "supabase:datasets/uploads/legacy-purge",
    )

    assert fake_backend.paths()

    # Deleting through the prefixed identifier must clear both spellings.
    cloud_storage.delete_file(
        "supabase:datasets/uploads/purge"
    )

    assert not any(
        path.startswith("datasets/uploads/purge")
        for path in fake_backend.paths()
    )

    cloud_storage.delete_file(
        "datasets/uploads/legacy-purge"
    )

    remaining = {
        path
        for path in fake_backend.paths()
        if "legacy-purge" in path
    }

    assert remaining == set()


def test_delete_file_removes_orphans_when_manifest_is_missing(
    cloud_storage, fake_backend
):
    """A dataset whose manifest was lost must still be purgeable."""

    fake_backend.objects[
        (TEST_BUCKET, "datasets/42/chunk_000000")
    ] = b"x"

    fake_backend.objects[
        (TEST_BUCKET, "datasets/42/chunk_000001")
    ] = b"y"

    cloud_storage.delete_file("datasets/42")

    assert fake_backend.paths() == set()


def test_chunk_size_is_clamped_below_supabase_object_limit(
    cloud_storage, monkeypatch
):
    monkeypatch.setattr(
        settings,
        "SUPABASE_CHUNK_SIZE_MB",
        500,
    )

    assert cloud_storage.chunk_size == MAX_SUPABASE_OBJECT_BYTES

    monkeypatch.setattr(
        settings,
        "SUPABASE_CHUNK_SIZE_MB",
        0,
    )

    assert cloud_storage.chunk_size == 1024 * 1024


def test_chunk_manifest_records_normalized_object_paths(
    cloud_storage, fake_backend
):
    manifest = cloud_storage.create_chunk_manifest(
        storage_id="supabase:datasets/uploads/manifest-check",
        total_chunks=2,
        file_size=2048,
    )

    assert manifest["storage_id"] == "datasets/uploads/manifest-check"

    assert [
        chunk["path"] for chunk in manifest["chunks"]
    ] == [
        "datasets/uploads/manifest-check/chunk_000000",
        "datasets/uploads/manifest-check/chunk_000001",
    ]

    assert (
        "datasets/uploads/manifest-check/manifest.json"
        in fake_backend.paths()
    )


# ---------------------------------------------------------------------------
# End-to-end flows through the API
# ---------------------------------------------------------------------------


CLOUD_CSV = b"id,amount,label\n1,10, alpha \n2,,beta\n,30,alpha\n"


def grant_pro_plan(db, user_dict):
    from app.models.subscription import (
        PlanType,
        Subscription,
        SubscriptionStatus,
    )
    from app.models.user import User

    user = db.query(User).filter_by(
        email=user_dict["email"]
    ).one()

    db.add(
        Subscription(
            user_id=user.id,
            plan=PlanType.PRO,
            status=SubscriptionStatus.ACTIVE,
        )
    )

    db.commit()


def initialize_chunked_upload(
    client,
    headers,
    filename,
    file_size,
):
    """Initialize the current browser-to-Supabase upload contract."""

    return client.post(
        "/api/v1/datasets/upload/init",
        headers=headers,
        json={
            "filename": filename,
            "file_size": file_size,
        },
    )


# ---------------------------------------------------------------------------
# Browser upload initialization and signed chunk URLs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "dataset.csv",
        "dataset.xls",
        "dataset.xlsx",
    ],
)
def test_upload_init_accepts_supported_filenames_and_returns_chunk_contract(
    client,
    auth_headers,
    cloud_storage,
    filename,
):
    response = initialize_chunked_upload(
        client,
        auth_headers,
        filename,
        1024,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert re.fullmatch(
        r"datasets/uploads/[0-9a-f]{32}",
        body["storage_id"],
    )

    assert body["original_filename"] == filename
    assert body["file_type"] == Path(filename).suffix.removeprefix(".")
    assert body["file_size"] == 1024
    assert body["chunk_size"] == cloud_storage.chunk_size


@pytest.mark.parametrize(
    ("filename", "file_size", "detail"),
    [
        (
            "dataset.csv",
            0,
            "File size must be greater than zero.",
        ),
        (
            "dataset.txt",
            1024,
            "Only CSV, XLSX and XLS files are supported.",
        ),
    ],
)
def test_upload_init_rejects_invalid_file_metadata(
    client,
    auth_headers,
    filename,
    file_size,
    detail,
):
    response = initialize_chunked_upload(
        client,
        auth_headers,
        filename,
        file_size,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == detail


def test_upload_init_enforces_upload_quota(
    client,
    auth_headers,
    cloud_storage,
    monkeypatch,
):
    from app.services.payment import payment_service

    monkeypatch.setitem(
        payment_service.plans["free"]["limits"],
        "max_file_size_mb",
        0,
    )

    response = initialize_chunked_upload(
        client,
        auth_headers,
        "limited.csv",
        1,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PLAN_LIMIT_REACHED"


def test_upload_init_requires_configured_supabase(
    client,
    auth_headers,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "SUPABASE_URL",
        "",
    )

    response = initialize_chunked_upload(
        client,
        auth_headers,
        "dataset.csv",
        1024,
    )

    assert response.status_code == 500
    assert (
        "Supabase Storage is not configured"
        in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "chunk_index",
    [0, 1, 2],
)
def test_chunk_url_uses_zero_padded_current_chunk_paths(
    client,
    auth_headers,
    cloud_storage,
    monkeypatch,
    chunk_index,
):
    # This test needs three chunks, which is larger than the Free-plan
    # upload limit. Bypass only the entitlement check for this test.
    monkeypatch.setattr(
        "app.api.v1.endpoints.dataset.enforce_upload_size",
        lambda db, owner_id, file_size: None,
    )

    initialized = initialize_chunked_upload(
        client,
        auth_headers,
        "dataset.csv",
        cloud_storage.chunk_size * 3,
    )

    assert initialized.status_code == 200, initialized.text

    storage_id = initialized.json()["storage_id"]

    response = client.post(
        "/api/v1/datasets/upload/chunk-url",
        headers=auth_headers,
        params={
            "storage_id": storage_id,
            "chunk_index": chunk_index,
        },
    )

    assert response.status_code == 200, response.text

    assert response.json() == {
        "storage_id": storage_id,
        "chunk_index": chunk_index,
        "path": f"{storage_id}/chunk_{chunk_index:06d}",
        "token": f"token::{storage_id}/chunk_{chunk_index:06d}",
    }


@pytest.mark.parametrize(
    ("storage_id", "chunk_index", "detail"),
    [
        (
            "datasets/uploads/example",
            -1,
            "Chunk index must be non-negative.",
        ),
        (
            "datasets/not-uploads/example",
            0,
            "Invalid dataset storage ID.",
        ),
        (
            "../datasets/uploads/example",
            0,
            "Invalid dataset storage ID.",
        ),
    ],
)
def test_chunk_url_rejects_invalid_current_contract_values(
    client,
    auth_headers,
    cloud_storage,
    storage_id,
    chunk_index,
    detail,
):
    response = client.post(
        "/api/v1/datasets/upload/chunk-url",
        headers=auth_headers,
        params={
            "storage_id": storage_id,
            "chunk_index": chunk_index,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == detail


def test_finalize_rejects_invalid_chunk_count_without_persisting_dataset(
    client,
    auth_headers,
    cloud_storage,
    db,
):
    initialized = initialize_chunked_upload(
        client,
        auth_headers,
        "dataset.csv",
        len(CLOUD_CSV),
    )

    storage_id = initialized.json()["storage_id"]

    response = client.post(
        "/api/v1/datasets/upload/finalize",
        headers=auth_headers,
        params={
            "storage_id": storage_id,
            "original_filename": "dataset.csv",
            "file_size": len(CLOUD_CSV),
            "total_chunks": 0,
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Total chunks must be greater than zero."
    )

    from app.models.dataset import Dataset

    assert db.query(Dataset).count() == 0


@pytest.mark.xfail(
    strict=True,
    reason=(
        "TODO (Step 2): upload prefixes are not persisted or bound to an owner, "
        "so the current endpoint cannot reject another authenticated user."
    ),
)
def test_chunk_url_rejects_another_users_upload_prefix(
    client,
    auth_headers,
    cloud_storage,
):
    initialized = initialize_chunked_upload(
        client,
        auth_headers,
        "dataset.csv",
        1024,
    )

    storage_id = initialized.json()["storage_id"]

    second_user = {
        "full_name": "Other Upload User",
        "email": "other-upload@example.com",
        "password": "OtherSecret123",
    }

    assert (
        client.post(
            "/api/v1/auth/register",
            json=second_user,
        ).status_code
        == 201
    )

    second_login = client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user["email"],
            "password": second_user["password"],
        },
    )

    response = client.post(
        "/api/v1/datasets/upload/chunk-url",
        headers={
            "Authorization": (
                f"Bearer {second_login.json()['access_token']}"
            )
        },
        params={
            "storage_id": storage_id,
            "chunk_index": 0,
        },
    )

    assert response.status_code == 403


def upload_chunked_dataset(
    client,
    headers,
    fake_backend,
    monkeypatch,
    tmp_path,
    filename,
    payload,
):
    """Drive the browser chunk flow against the in-memory storage."""

    monkeypatch.setattr(
        settings,
        "DATASET_STORAGE_DIR",
        str(tmp_path),
    )

    monkeypatch.setattr(
        settings,
        "USE_CLOUD_STORAGE",
        True,
    )

    init = client.post(
        "/api/v1/datasets/upload/init",
        headers=headers,
        json={
            "filename": filename,
            "file_size": len(payload),
        },
    )

    assert init.status_code == 200, init.text

    storage_id = init.json()["storage_id"]
    chunk_size = init.json()["chunk_size"]

    total_chunks = max(
        1,
        -(-len(payload) // chunk_size),
    )

    for chunk_index in range(total_chunks):
        start = chunk_index * chunk_size
        chunk = payload[start:start + chunk_size]

        # The browser PUTs this chunk through a signed URL; the harness
        # writes it straight into the stand-in bucket instead.
        fake_backend.objects[
            (
                TEST_BUCKET,
                f"{storage_id}/chunk_{chunk_index:06d}",
            )
        ] = chunk

    finalize = client.post(
        "/api/v1/datasets/upload/finalize",
        headers=headers,
        params={
            "storage_id": storage_id,
            "original_filename": filename,
            "file_size": len(payload),
            "total_chunks": total_chunks,
        },
    )

    return storage_id, finalize


def test_chunked_upload_persists_in_cloud_and_survives_local_wipe(
    client,
    auth_headers,
    db,
    monkeypatch,
    tmp_path,
    fake_backend,
    cloud_storage,
):
    from app.models.dataset import Dataset

    storage_id, finalize = upload_chunked_dataset(
        client,
        auth_headers,
        fake_backend,
        monkeypatch,
        tmp_path,
        "cloud.csv",
        CLOUD_CSV,
    )

    assert finalize.status_code == 201, finalize.text

    dataset = finalize.json()

    stored = db.query(Dataset).filter_by(
        id=dataset["id"]
    ).one()

    # The record must reference Supabase, not an ephemeral local path.
    assert stored.file_path == f"supabase:{storage_id}"

    assert dataset["rows"] == 3
    assert dataset["columns"] == 3

    # The browser-uploaded chunks are untouched by finalisation.
    assert (
        f"{storage_id}/manifest.json"
        in fake_backend.paths()
    )

    # Simulate a container restart: the staging directory is thrown away.
    for staged in tmp_path.iterdir():
        staged.unlink()

    download = client.get(
        f"/api/v1/datasets/{dataset['id']}/download",
        headers=auth_headers,
    )

    assert download.status_code == 200, download.text
    assert download.content == CLOUD_CSV


def test_cloud_cleaning_report_and_delete_round_trip(
    client,
    auth_headers,
    user_dict,
    db,
    monkeypatch,
    tmp_path,
    fake_backend,
    cloud_storage,
):
    from app.models.dataset import Dataset

    grant_pro_plan(
        db,
        user_dict,
    )

    storage_id, finalize = upload_chunked_dataset(
        client,
        auth_headers,
        fake_backend,
        monkeypatch,
        tmp_path,
        "cloud.csv",
        CLOUD_CSV,
    )

    assert finalize.status_code == 201, finalize.text

    dataset_id = finalize.json()["id"]

    preview = client.post(
        f"/api/v1/cleaning/{dataset_id}/preview",
        headers=auth_headers,
    )

    assert preview.status_code == 200, preview.text
    assert preview.json()["preview"]["rows_before"] == 3
    assert (
        preview.json()["preview"]["missing_values_filled"] > 0
    )

    applied = client.post(
        f"/api/v1/cleaning/{dataset_id}/apply",
        headers=auth_headers,
    )

    assert applied.status_code == 200, applied.text

    cleaned_prefix = f"datasets/{dataset_id}/cleaned"

    assert (
        f"{cleaned_prefix}/manifest.json"
        in fake_backend.paths()
    )

    cleaned_download = client.get(
        f"/api/v1/cleaning/{dataset_id}/download",
        headers=auth_headers,
    )

    assert cleaned_download.status_code == 200, cleaned_download.text
    assert cleaned_download.content.startswith(
        b"id,amount,label"
    )

    # The original dataset is never modified by cleaning.
    original_download = client.get(
        f"/api/v1/datasets/{dataset_id}/download",
        headers=auth_headers,
    )

    assert original_download.content == CLOUD_CSV

    report = client.get(
        f"/api/v1/reports/{dataset_id}/pdf",
        headers=auth_headers,
    )

    assert report.status_code == 200, report.text
    assert report.content.startswith(b"%PDF-")

    deleted = client.delete(
        f"/api/v1/datasets/{dataset_id}",
        headers=auth_headers,
    )

    assert deleted.status_code == 204

    assert (
        db.query(Dataset)
        .filter_by(id=dataset_id)
        .count()
        == 0
    )

    remaining = {
        path
        for path in fake_backend.paths()
        if path.startswith(storage_id)
        or path.startswith(cleaned_prefix)
    }

    assert remaining == set()


def test_finalize_with_cloud_storage_disabled_keeps_dataset_local(
    client,
    auth_headers,
    db,
    monkeypatch,
    tmp_path,
    fake_backend,
    cloud_storage,
):
    """A deployment without cloud storage must never reference Supabase."""

    from app.models.dataset import Dataset
    from app.services.dataset_storage import resolve_dataset_path

    monkeypatch.setattr(
        settings,
        "DATASET_STORAGE_DIR",
        str(tmp_path),
    )

    monkeypatch.setattr(
        settings,
        "USE_CLOUD_STORAGE",
        False,
    )

    init = client.post(
        "/api/v1/datasets/upload/init",
        headers=auth_headers,
        json={
            "filename": "local.csv",
            "file_size": len(CLOUD_CSV),
        },
    )

    storage_id = init.json()["storage_id"]

    fake_backend.objects[
        (TEST_BUCKET, f"{storage_id}/chunk_000000")
    ] = CLOUD_CSV

    finalize = client.post(
        "/api/v1/datasets/upload/finalize",
        headers=auth_headers,
        params={
            "storage_id": storage_id,
            "original_filename": "local.csv",
            "file_size": len(CLOUD_CSV),
            "total_chunks": 1,
        },
    )

    assert finalize.status_code == 201, finalize.text

    stored = db.query(Dataset).filter_by(
        id=finalize.json()["id"]
    ).one()

    assert not stored.file_path.startswith("supabase:")

    resolved = resolve_dataset_path(
        stored.file_path
    )

    assert resolved.is_file()
    assert resolved.read_bytes() == CLOUD_CSV


def test_cloud_dataset_with_missing_manifest_reports_safe_not_found(
    client,
    auth_headers,
    db,
    monkeypatch,
    tmp_path,
    fake_backend,
    cloud_storage,
):
    from app.models.dataset import Dataset
    from app.models.user import User

    uploaded = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={
            "file": (
                "local.csv",
                CLOUD_CSV,
                "text/csv",
            )
        },
    )

    assert uploaded.status_code == 201, uploaded.text

    dataset_id = uploaded.json()["id"]

    user = db.query(User).filter_by(
        email="alice@example.com"
    ).one()

    # Point the record at a Supabase prefix that has no objects at all.
    stored = db.query(Dataset).filter_by(
        id=dataset_id
    ).one()

    stored.file_path = "supabase:datasets/gone"
    db.commit()

    response = client.post(
        f"/api/v1/cleaning/{dataset_id}/preview",
        headers=auth_headers,
    )

    assert user is not None
    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Dataset file not found on server."
    )
    assert "Traceback" not in response.text


# ---------------------------------------------------------------------------
# AI explanation fallback
# ---------------------------------------------------------------------------


def test_ai_explanation_reports_unavailable_when_providers_fail(
    client,
    auth_headers,
    monkeypatch,
    tmp_path,
    workflow_files,
):
    from app.services import insights as insights_module

    monkeypatch.setattr(
        settings,
        "DATASET_STORAGE_DIR",
        str(tmp_path),
    )

    uploaded = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={
            "file": (
                "normal.csv",
                workflow_files["normal.csv"],
                "text/csv",
            )
        },
    )

    assert uploaded.status_code == 201, uploaded.text

    async def failing_provider(_prompt):
        raise insights_module.AIProviderError(
            "provider detail must not escape"
        )

    monkeypatch.setattr(
        insights_module,
        "generate_ai_response",
        failing_provider,
    )

    response = client.get(
        f"/api/v1/analysis/{uploaded.json()['id']}/explanation",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["available"] is False
    assert "temporarily unavailable" in body["explanation"]
    assert "provider detail" not in response.text


def test_ai_explanation_rejects_numbers_absent_from_the_profile(
    client,
    auth_headers,
    monkeypatch,
    tmp_path,
    workflow_files,
):
    from app.services import insights as insights_module

    monkeypatch.setattr(
        settings,
        "DATASET_STORAGE_DIR",
        str(tmp_path),
    )

    uploaded = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={
            "file": (
                "normal.csv",
                workflow_files["normal.csv"],
                "text/csv",
            )
        },
    )

    assert uploaded.status_code == 201, uploaded.text

    async def fabricating_provider(_prompt):
        return "The dataset contains 999999 rows."

    monkeypatch.setattr(
        insights_module,
        "generate_ai_response",
        fabricating_provider,
    )

    response = client.get(
        f"/api/v1/analysis/{uploaded.json()['id']}/explanation",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["available"] is False


def test_ai_explanation_accepts_verified_numbers_with_list_markers(
    client,
    auth_headers,
    monkeypatch,
    tmp_path,
    workflow_files,
):
    from app.services import insights as insights_module

    monkeypatch.setattr(
        settings,
        "DATASET_STORAGE_DIR",
        str(tmp_path),
    )

    uploaded = client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={
            "file": (
                "normal.csv",
                workflow_files["normal.csv"],
                "text/csv",
            )
        },
    )

    dataset_id = uploaded.json()["id"]

    async def marked_provider(_prompt):
        return (
            "1. The dataset contains 3 rows.\n"
            "2. It also has 3 columns."
        )

    monkeypatch.setattr(
        insights_module,
        "generate_ai_response",
        marked_provider,
    )

    response = client.get(
        f"/api/v1/analysis/{dataset_id}/explanation",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["available"] is True

    # The cached explanation is reused on the next request.
    cached = client.get(
        f"/api/v1/analysis/{dataset_id}/explanation",
        headers=auth_headers,
    )

    assert cached.status_code == 200
    assert cached.json()["available"] is True