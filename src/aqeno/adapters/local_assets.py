"""Atomic local media/artwork storage used by the Management API adapter."""

from __future__ import annotations

import os
import tempfile
import uuid
from contextlib import suppress
from pathlib import Path
from typing import BinaryIO


class UploadTooLargeError(Exception):
    pass


class LocalAssetStore:
    def __init__(self, *, media_root: Path, artwork_root: Path) -> None:
        self.media_root = media_root
        self.artwork_root = artwork_root

    def store_media(
        self, source: BinaryIO, *, filename: str, maximum_bytes: int = 4 * 1024**3
    ) -> Path:
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            raise ValueError("invalid upload filename")
        target_dir = self.media_root / "imports" / str(uuid.uuid4())
        target_dir.mkdir(parents=True, exist_ok=False)
        return self._atomic_copy(source, target_dir / safe_name, maximum_bytes)

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
