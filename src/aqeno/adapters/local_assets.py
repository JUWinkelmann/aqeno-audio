"""Atomic local media/artwork storage used by the Management API adapter."""

from __future__ import annotations

import os
import tempfile
import uuid
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import BinaryIO

from aqeno.appliance.storage import CapacityStatus


class UploadTooLargeError(Exception):
    pass


class InsufficientCapacityError(Exception):
    pass


class LocalAssetStore:
    def __init__(
        self,
        *,
        media_root: Path,
        artwork_root: Path,
        import_staging_root: Path | None = None,
        capacity: Callable[[], CapacityStatus] | None = None,
    ) -> None:
        self.media_root = media_root
        self.artwork_root = artwork_root
        self.import_staging_root = import_staging_root or media_root / ".staging"
        self._capacity = capacity

    def store_media(
        self, source: BinaryIO, *, filename: str, maximum_bytes: int = 4 * 1024**3
    ) -> Path:
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            raise ValueError("invalid upload filename")
        expected = self._stream_size(source)
        if expected is not None and self._capacity is not None:
            status: CapacityStatus = self._capacity()
            if not status.permits(expected, staging_copies=1):
                raise InsufficientCapacityError("not enough reserved capacity for import")
        operation_id = str(uuid.uuid4())
        staging_dir = self.import_staging_root / operation_id
        target_dir = self.media_root / "imports" / operation_id
        staging_dir.mkdir(parents=True, exist_ok=False)
        try:
            staged = self._atomic_copy(source, staging_dir / safe_name, maximum_bytes)
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging_dir, target_dir)
            return target_dir / staged.name
        except BaseException:
            with suppress(OSError):
                for child in staging_dir.iterdir():
                    child.unlink()
                staging_dir.rmdir()
            raise

    def cleanup_interrupted_imports(self) -> int:
        """Remove only Class-D staging; published media is never touched."""
        if not self.import_staging_root.is_dir():
            return 0
        removed = 0
        for operation in self.import_staging_root.iterdir():
            if operation.is_dir():
                for child in operation.iterdir():
                    if child.is_file():
                        child.unlink()
                with suppress(OSError):
                    operation.rmdir()
                    removed += 1
            elif operation.is_file():
                operation.unlink()
                removed += 1
        return removed

    @staticmethod
    def _stream_size(source: BinaryIO) -> int | None:
        try:
            position = source.tell()
            source.seek(0, os.SEEK_END)
            size = source.tell()
            source.seek(position)
            return size - position
        except (AttributeError, OSError):
            return None

    def store_artwork(
        self,
        source: BinaryIO,
        *,
        content_id: uuid.UUID,
        extension: str,
        maximum_bytes: int = 20 * 1024**2,
    ) -> Path:
        suffix = (
            extension.lower() if extension.lower() in {".jpg", ".jpeg", ".png", ".webp"} else ""
        )
        if not suffix:
            raise ValueError("unsupported artwork type")
        expected = self._stream_size(source)
        if expected is not None and self._capacity is not None:
            status = self._capacity()
            if not status.permits(expected, staging_copies=1):
                raise InsufficientCapacityError("not enough reserved capacity for artwork")
        self.artwork_root.mkdir(parents=True, exist_ok=True)
        return self._atomic_copy(source, self.artwork_root / f"{content_id}{suffix}", maximum_bytes)

    @staticmethod
    def _atomic_copy(source: BinaryIO, target: Path, maximum_bytes: int) -> Path:
        fd, temporary = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
        )
        size = 0
        try:
            with os.fdopen(fd, "wb") as destination:
                while chunk := source.read(1024 * 1024):
                    size += len(chunk)
                    if size > maximum_bytes:
                        raise UploadTooLargeError(f"upload exceeds {maximum_bytes} bytes")
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary, target)
        except BaseException:
            with suppress(FileNotFoundError):
                os.unlink(temporary)
            raise
        return target

    def open_artwork(self, path: Path) -> BinaryIO:
        return path.open("rb")

    def remove_artwork(self, path: Path) -> None:
        with suppress(FileNotFoundError):
            path.unlink()
