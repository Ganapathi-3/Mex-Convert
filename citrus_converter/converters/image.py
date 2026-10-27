"""
Image converter — uses ImageMagick ``convert`` (or ``magick``) as the backend.

For HEIC input, tries ``heif-convert`` first, then falls back to ImageMagick.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .base import BaseConverter, ConversionError

_IMAGE_FORMATS = [
    "jpeg", "jpg", "png", "heic", "webp", "tiff", "tif",
    "bmp", "svg", "gif", "pdf", "avif", "ico",
]

# Every image format can convert to every other image format.
_CONVERSIONS = {
    fmt: [f for f in _IMAGE_FORMATS if f != fmt]
    for fmt in _IMAGE_FORMATS
}


class ImageConverter(BaseConverter):
    """Convert between raster/vector image formats via ImageMagick."""

    _conversions = _CONVERSIONS
    _required_tools = ["convert"]

    # ── public ───────────────────────────────────────────────────

    def convert(
        self,
        input_path: str | Path,
        output_format: str,
        output_dir: str | Path | None = None,
        **options: Any,
    ) -> str:
        """Convert an image file to *output_format*.

        Keyword options:
            quality (int): Output quality 1-100 (JPEG/WebP/AVIF).

        Returns:
            Absolute path of the converted file.
        """
        input_path = Path(input_path).resolve()
        self._validate_input(input_path)

        out_fmt = output_format.lower().lstrip(".")
        in_ext = input_path.suffix.lower().lstrip(".")

        supported = self.get_supported_conversions(in_ext)
        if not supported:
            raise ConversionError(f"Unsupported input format: {in_ext}")
        if out_fmt not in supported and out_fmt not in _IMAGE_FORMATS:
            raise ConversionError(
                f"Cannot convert {in_ext!r} → {out_fmt!r}. "
                f"Supported outputs: {supported}"
            )

        output_path = self._resolve_output_path(
            input_path, out_fmt, output_dir and Path(output_dir),
        )

        print(f"[elumichai] Converting {input_path.name} → {output_path.name} …")

        # HEIC input: try heif-convert first
        if in_ext == "heic" and shutil.which("heif-convert"):
            try:
                self._convert_heic(input_path, output_path, out_fmt, options)
                print(f"[elumichai] Done → {output_path}")
                return str(output_path)
            except ConversionError:
                print("[elumichai] heif-convert failed; falling back to ImageMagick.")

        # General path — ImageMagick
        self._convert_imagemagick(input_path, output_path, out_fmt, options)
        print(f"[elumichai] Done → {output_path}")
        return str(output_path)

    # ── private helpers ──────────────────────────────────────────

    def _magick_cmd(self) -> str:
        """Return the ImageMagick command name available on this system."""
        if shutil.which("magick"):
            return "magick"
        if shutil.which("convert"):
            return "convert"
        raise ConversionError(
            "ImageMagick is not installed. Install it and ensure 'convert' "
            "or 'magick' is on PATH."
        )

    def _convert_imagemagick(
        self,
        input_path: Path,
        output_path: Path,
        out_fmt: str,
        options: dict[str, Any],
    ) -> None:
        """Run the ImageMagick conversion."""
        cmd: list[str] = [self._magick_cmd(), str(input_path)]

        quality = options.get("quality")
        if quality is not None:
            cmd += ["-quality", str(int(quality))]

        cmd.append(str(output_path))
        self._run_command(cmd)

    def _convert_heic(
        self,
        input_path: Path,
        output_path: Path,
        out_fmt: str,
        options: dict[str, Any],
    ) -> None:
        """Convert HEIC via ``heif-convert``."""
        quality = options.get("quality", 85)
        cmd = [
            "heif-convert",
            "-q", str(int(quality)),
            str(input_path),
            str(output_path),
        ]
        self._run_command(cmd)
