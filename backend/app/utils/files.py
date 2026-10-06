"""Small filesystem helpers shared by the dataset storage services."""

import os
import tempfile
from pathlib import Path


def create_temporary_file_path(
    prefix: str,
    suffix: str = "",
) -> Path:
    """Return an unused temporary file path without leaking a descriptor.

    ``tempfile.mkstemp`` returns an open file descriptor alongside the path.
    Earlier revisions discarded the descriptor, which leaked one descriptor
    per dataset operation until the worker exhausted its open-file limit.
    The returned path is guaranteed not to exist so callers can create it.
    """

    descriptor, raw_path = tempfile.mkstemp(
        prefix=prefix,
        suffix=suffix,
    )

    try:
        os.close(descriptor)
    except OSError:  # pragma: no cover - descriptor already closed
        pass

    path = Path(raw_path)

    path.unlink(missing_ok=True)

    return path
