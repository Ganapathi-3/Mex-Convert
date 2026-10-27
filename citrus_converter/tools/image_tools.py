"""
Image manipulation tools — resize, crop, compress, strip metadata, info.

Uses ImageMagick (``convert`` / ``magick``, ``identify``).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from citrus_converter.converters.base import ConversionError


def _magick() -> str:
    """Return the available ImageMagick binary name."""
    if shutil.which("magick"):
        return "magick"
    if shutil.which("convert"):
        return "convert"
    raise ConversionError("ImageMagick is not installed ('convert' / 'magick' not found).")


def _identify() -> str:
    """Return the identify binary name."""
    if shutil.which("magick"):
        return "magick"  # magick identify …
    if shutil.which("identify"):
        return "identify"
    raise ConversionError("ImageMagick 'identify' command not found.")


def _run(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        raise ConversionError(f"Command not found: {cmd[0]!r}")
    if result.returncode != 0:
        raise ConversionError(
            f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.returncode, result.stdout, result.stderr


def _output_path(original: Path, suffix: str) -> Path:
    """Generate an output path next to *original* with *suffix* appended to stem."""
    return original.parent / f"{original.stem}{suffix}{original.suffix}"


class ImageTools:
    """Collection of image manipulation utilities backed by ImageMagick."""

    @staticmethod
    def compress(path: str | Path, quality: int = 75) -> str:
        """Re-compress an image at the given *quality* (1-100).

        Returns:
            Path to the compressed image (``<stem>_compressed.<ext>``).
        """
        path = Path(path).resolve()
        out = _output_path(path, "_compressed")
        print(f"[citrus] Compressing {path.name} (quality={quality}) …")
        _run([_magick(), str(path), "-quality", str(quality), str(out)])
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def resize(path: str | Path, width: int, height: int) -> str:
        """Resize an image to *width* × *height* pixels.

        Returns:
            Path to the resized image.
        """
        path = Path(path).resolve()
        out = _output_path(path, f"_{width}x{height}")
        geometry = f"{width}x{height}!"
        print(f"[citrus] Resizing {path.name} → {geometry} …")
        _run([_magick(), str(path), "-resize", geometry, str(out)])
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def crop(path: str | Path, x: int, y: int, w: int, h: int) -> str:
        """Crop a region starting at (*x*, *y*) with size *w* × *h*.

        Returns:
            Path to the cropped image.
        """
        path = Path(path).resolve()
        out = _output_path(path, "_cropped")
        geometry = f"{w}x{h}+{x}+{y}"
        print(f"[citrus] Cropping {path.name} → {geometry} …")
        _run([_magick(), str(path), "-crop", geometry, "+repage", str(out)])
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def strip_metadata(path: str | Path) -> str:
        """Remove all EXIF / metadata from an image.

        Returns:
            Path to the stripped image.
        """
        path = Path(path).resolve()
        out = _output_path(path, "_stripped")
        print(f"[citrus] Stripping metadata from {path.name} …")
        _run([_magick(), str(path), "-strip", str(out)])
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def get_info(path: str | Path) -> dict:
        """Return basic image information (format, dimensions, size, …).

        Returns:
            Dict with keys: ``format``, ``width``, ``height``,
            ``depth``, ``filesize``, ``colorspace``.
        """
        path = Path(path).resolve()
        identify = _identify()
        cmd = [identify]
        # If using magick wrapper, need "identify" sub-command
        if identify == "magick":
            cmd.append("identify")
        cmd += ["-format", "%m %w %h %z %b %r", str(path)]
        _, stdout, _ = _run(cmd)
        parts = stdout.strip().split()
        return {
            "format": parts[0] if len(parts) > 0 else "unknown",
            "width": int(parts[1]) if len(parts) > 1 else 0,
            "height": int(parts[2]) if len(parts) > 2 else 0,
            "depth": parts[3] if len(parts) > 3 else "unknown",
            "filesize": parts[4] if len(parts) > 4 else "unknown",
            "colorspace": parts[5] if len(parts) > 5 else "unknown",
            "path": str(path),
        }
