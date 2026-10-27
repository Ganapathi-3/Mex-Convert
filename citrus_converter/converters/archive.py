"""
Archive converter — create and extract archives.

Uses Python's ``zipfile`` / ``tarfile`` for ZIP and TAR variants, and the
``7z`` command for 7-Zip archives.
"""

from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import Any

from .base import BaseConverter, ConversionError

_ARCHIVE_FORMATS = ["zip", "tar", "tar.gz", "tar.bz2", "tar.xz", "gz", "gzip", "7z", "rar"]

_CONVERSIONS = {
    fmt: [f for f in _ARCHIVE_FORMATS if f != fmt and f != "rar"]
    for fmt in _ARCHIVE_FORMATS
}
_CONVERSIONS["rar"] = ["zip", "tar", "gz", "gzip"]

# tarfile open modes
_TAR_MODES: dict[str, str] = {
    "tar":     "w",
    "tar.gz":  "w:gz",
    "tar.bz2": "w:bz2",
    "tar.xz":  "w:xz",
    "gz":      "w:gz",
    "gzip":    "w:gz",
}

_TAR_READ_MODES: dict[str, str] = {
    "tar":     "r:",
    "tar.gz":  "r:gz",
    "tar.bz2": "r:bz2",
    "tar.xz":  "r:xz",
    "gz":      "r:gz",
    "gzip":    "r:gz",
}


def _normalised_ext(path: Path) -> str:
    """Return the full compound extension (e.g. ``tar.gz``)."""
    name = path.name.lower()
    for compound in ("tar.gz", "tar.bz2", "tar.xz"):
        if name.endswith(f".{compound}"):
            return compound
    return path.suffix.lower().lstrip(".")


class ArchiveConverter(BaseConverter):
    """Re-package archives from one format to another.

    The conversion works by *extracting* the source archive into a temporary
    directory and then *creating* a new archive in the target format.
    """

    _conversions = _CONVERSIONS
    _required_tools = []  # 7z checked dynamically

    def convert(
        self,
        input_path: str | Path,
        output_format: str,
        output_dir: str | Path | None = None,
        **options: Any,
    ) -> str:
        """Convert (repackage) an archive to *output_format*.

        Returns:
            Absolute path of the newly created archive.
        """
        input_path = Path(input_path).resolve()
        self._validate_input(input_path)

        out_fmt = output_format.lower().lstrip(".")
        in_ext = _normalised_ext(input_path)

        supported = self.get_supported_conversions(in_ext)
        if not supported:
            raise ConversionError(f"Unsupported input format: {in_ext}")
        if out_fmt not in supported and out_fmt not in _ARCHIVE_FORMATS:
            raise ConversionError(
                f"Cannot convert {in_ext!r} → {out_fmt!r}. "
                f"Supported outputs: {supported}"
            )

        output_path = self._resolve_output_path(
            input_path, out_fmt, output_dir and Path(output_dir),
        )

        print(f"[citrus] Converting {input_path.name} → {output_path.name} …")

        # 1. Extract to a temp dir
        import tempfile
        with tempfile.TemporaryDirectory(prefix="citrus_") as tmp:
            tmp_dir = Path(tmp)
            self._extract(input_path, in_ext, tmp_dir)

            # 2. Re-create archive in target format
            self._create(output_path, out_fmt, tmp_dir)

        print(f"[citrus] Done → {output_path}")
        return str(output_path)

    # ── extraction ───────────────────────────────────────────────

    def _extract(self, archive: Path, fmt: str, dest: Path) -> None:
        """Extract *archive* into *dest*."""
        if fmt == "zip":
            self._extract_zip(archive, dest)
        elif fmt in _TAR_READ_MODES:
            self._extract_tar(archive, fmt, dest)
        elif fmt in ("7z", "rar"):
            self._extract_7z(archive, dest)
        else:
            raise ConversionError(f"Cannot extract format: {fmt}")

    def _extract_zip(self, archive: Path, dest: Path) -> None:
        """Extract a ZIP archive."""
        try:
            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(dest)
        except zipfile.BadZipFile as exc:
            raise ConversionError(f"Bad ZIP file: {exc}") from exc

    def _extract_tar(self, archive: Path, fmt: str, dest: Path) -> None:
        """Extract a TAR (optionally compressed) archive."""
        mode = _TAR_READ_MODES[fmt]
        try:
            with tarfile.open(archive, mode) as tf:
                tf.extractall(dest, filter="data")
        except tarfile.TarError as exc:
            raise ConversionError(f"Bad TAR file: {exc}") from exc

    def _extract_7z(self, archive: Path, dest: Path) -> None:
        """Extract a 7-Zip archive using the ``7z`` command."""
        if not shutil.which("7z"):
            raise ConversionError(
                "'7z' command not found. Please install p7zip."
            )
        self._run_command(["7z", "x", str(archive), f"-o{dest}", "-y"])

    # ── creation ─────────────────────────────────────────────────

    def _create(self, output: Path, fmt: str, source_dir: Path) -> None:
        """Create a new archive from the contents of *source_dir*."""
        if fmt == "zip":
            self._create_zip(output, source_dir)
        elif fmt in _TAR_MODES:
            self._create_tar(output, fmt, source_dir)
        elif fmt == "7z":
            self._create_7z(output, source_dir)
        elif fmt == "rar":
            raise ConversionError("RAR is input-only; install a native RAR writer to create it.")
        else:
            raise ConversionError(f"Cannot create format: {fmt}")

    def _create_zip(self, output: Path, source_dir: Path) -> None:
        """Create a ZIP archive."""
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(source_dir.rglob("*")):
                if file.is_file():
                    zf.write(file, file.relative_to(source_dir))

    def _create_tar(self, output: Path, fmt: str, source_dir: Path) -> None:
        """Create a TAR archive (optionally compressed)."""
        mode = _TAR_MODES[fmt]
        with tarfile.open(output, mode) as tf:
            for file in sorted(source_dir.rglob("*")):
                tf.add(file, file.relative_to(source_dir))

    def _create_7z(self, output: Path, source_dir: Path) -> None:
        """Create a 7-Zip archive using the ``7z`` command."""
        if not shutil.which("7z"):
            raise ConversionError(
                "'7z' command not found. Please install p7zip."
            )
        # 7z a <output> <source_dir>/*
        self._run_command([
            "7z", "a", str(output), f"{source_dir}/*", "-y",
        ])
