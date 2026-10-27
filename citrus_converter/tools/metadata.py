"""
Metadata tools — read and strip metadata from media files.

Backend priority:
  1. ``exiftool``  (best for images / most formats)
  2. ``ffprobe``   (good for audio / video)
  3. ImageMagick ``identify`` (images only)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from citrus_converter.converters.base import ConversionError


def _run(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise ConversionError(f"Command not found: {cmd[0]!r}")
    if result.returncode != 0:
        raise ConversionError(
            f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.returncode, result.stdout, result.stderr


class MetadataTools:
    """Read and strip metadata from image, audio, and video files."""

    # ── read ─────────────────────────────────────────────────────

    @staticmethod
    def read_metadata(path: str | Path) -> dict:
        """Read metadata from *path* and return it as a dict.

        Tries exiftool → ffprobe → ImageMagick identify, in that order.

        Returns:
            Dict of metadata key/value pairs.
        """
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if shutil.which("exiftool"):
            return MetadataTools._read_exiftool(path)
        if shutil.which("ffprobe"):
            return MetadataTools._read_ffprobe(path)
        if shutil.which("identify") or shutil.which("magick"):
            return MetadataTools._read_identify(path)

        raise ConversionError(
            "No metadata tool found. Install exiftool, ffprobe, or ImageMagick."
        )

    @staticmethod
    def _read_exiftool(path: Path) -> dict:
        """Read metadata via exiftool (-json output)."""
        _, stdout, _ = _run(["exiftool", "-json", "-G", str(path)])
        data = json.loads(stdout)
        if isinstance(data, list) and data:
            return data[0]
        return {}

    @staticmethod
    def _read_ffprobe(path: Path) -> dict:
        """Read metadata via ffprobe."""
        _, stdout, _ = _run([
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(path),
        ])
        data = json.loads(stdout)
        fmt = data.get("format", {})
        meta: dict = {
            "format_name": fmt.get("format_name", "unknown"),
            "duration": fmt.get("duration"),
            "size": fmt.get("size"),
            "bitrate": fmt.get("bit_rate"),
        }
        tags = fmt.get("tags", {})
        meta.update(tags)
        return meta

    @staticmethod
    def _read_identify(path: Path) -> dict:
        """Read metadata via ImageMagick identify -verbose."""
        identify = "magick" if shutil.which("magick") else "identify"
        cmd = [identify]
        if identify == "magick":
            cmd.append("identify")
        cmd += ["-verbose", str(path)]
        _, stdout, _ = _run(cmd)

        # Parse key: value lines
        meta: dict = {}
        for line in stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
        return meta

    # ── strip ────────────────────────────────────────────────────

    @staticmethod
    def strip_metadata(path: str | Path, output: str | Path | None = None) -> str:
        """Remove all metadata / EXIF from *path*.

        Args:
            path: Input file.
            output: Destination path.  If ``None``, writes alongside the
                    original with ``_nometa`` suffix.

        Returns:
            Absolute path of the stripped file.
        """
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if output is None:
            out = path.parent / f"{path.stem}_nometa{path.suffix}"
        else:
            out = Path(output).resolve()

        print(f"[citrus] Stripping metadata from {path.name} …")

        if shutil.which("exiftool"):
            MetadataTools._strip_exiftool(path, out)
        elif shutil.which("ffmpeg"):
            MetadataTools._strip_ffmpeg(path, out)
        elif shutil.which("convert") or shutil.which("magick"):
            MetadataTools._strip_imagemagick(path, out)
        else:
            raise ConversionError(
                "No metadata tool found. Install exiftool, ffmpeg, or ImageMagick."
            )

        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def _strip_exiftool(path: Path, output: Path) -> None:
        """Strip metadata via exiftool."""
        # Copy first, then strip in-place
        import shutil as _shutil
        _shutil.copy2(path, output)
        _run(["exiftool", "-all=", "-overwrite_original", str(output)])

    @staticmethod
    def _strip_ffmpeg(path: Path, output: Path) -> None:
        """Strip metadata via ffmpeg (works for audio/video)."""
        _run([
            "ffmpeg", "-y", "-i", str(path),
            "-map_metadata", "-1",
            "-c", "copy",
            str(output),
        ])

    @staticmethod
    def _strip_imagemagick(path: Path, output: Path) -> None:
        """Strip metadata via ImageMagick -strip (images only)."""
        magick = "magick" if shutil.which("magick") else "convert"
        _run([magick, str(path), "-strip", str(output)])
