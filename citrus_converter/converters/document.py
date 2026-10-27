"""
Document converter — uses ``pandoc`` for text-based conversions and
``libreoffice --headless`` for office formats.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .base import BaseConverter, ConversionError

_DOC_FORMATS = [
    "pdf", "txt", "docx", "pages", "odt", "rtf", "rtfd", "clipping",
    "html", "md", "epub", "ppt", "pptx", "xlsx", "xls", "ods", "csv", "tsv",
    "jpg", "png", "srt", "vtt",
]

_CONVERSIONS = {
    fmt: [f for f in _DOC_FORMATS if f != fmt]
    for fmt in _DOC_FORMATS
}

# Pandoc input/output format names (not always == extension)
_PANDOC_FMT: dict[str, str] = {
    "md":   "markdown",
    "html": "html",
    "txt":  "plain",
    "pdf":  "pdf",
    "docx": "docx",
    "odt":  "odt",
    "rtf":  "rtf",
    "epub": "epub",
    "pages": "docx",
    "rtfd": "rtf",
    "clipping": "plain",
    "ppt": "ppt",
    "pptx": "pptx",
    "xlsx": "xlsx",
    "xls": "xls",
    "ods": "ods",
    "csv": "csv",
    "tsv": "tsv",
    "srt": "plain",
    "vtt": "plain",
}

# Formats that LibreOffice can reliably produce
_LO_OUTPUT_FMTS = {"pdf", "docx", "odt", "rtf", "html", "txt"}
# Formats that we prefer pandoc for
_PANDOC_PAIRS: set[tuple[str, str]] = {
    ("md", "html"), ("md", "pdf"), ("md", "docx"), ("md", "epub"),
    ("html", "md"), ("html", "pdf"), ("html", "docx"), ("html", "epub"),
    ("txt", "html"), ("txt", "pdf"), ("txt", "docx"), ("txt", "epub"),
    ("epub", "html"), ("epub", "pdf"), ("epub", "docx"), ("epub", "md"),
    ("docx", "md"), ("docx", "html"), ("docx", "epub"),
    ("odt", "md"), ("odt", "html"), ("odt", "epub"),
    ("rtf", "md"), ("rtf", "html"), ("rtf", "epub"),
}


class DocumentConverter(BaseConverter):
    """Convert between document formats using pandoc and LibreOffice."""

    _conversions = _CONVERSIONS
    _required_tools = []  # checked dynamically

    def convert(
        self,
        input_path: str | Path,
        output_format: str,
        output_dir: str | Path | None = None,
        **options: Any,
    ) -> str:
        """Convert a document to *output_format*.

        The converter chooses between pandoc and LibreOffice automatically:
        - Pandoc is preferred for text↔markup conversions.
        - LibreOffice is used for office-format conversions or as a fallback.

        Returns:
            Absolute path of the converted file.
        """
        input_path = Path(input_path).resolve()
        self._validate_input(input_path)

        out_fmt = output_format.lower().lstrip(".")
        in_ext = input_path.suffix.lower().lstrip(".")
        if input_path.name.lower().endswith(".rtfd"):
            in_ext = "rtfd"

        # Normalise markdown extension variants
        if in_ext in ("markdown",):
            in_ext = "md"
        if out_fmt in ("markdown",):
            out_fmt = "md"

        supported = self.get_supported_conversions(in_ext)
        if not supported:
            raise ConversionError(f"Unsupported input format: {in_ext}")
        if out_fmt not in supported and out_fmt not in _DOC_FORMATS:
            raise ConversionError(
                f"Cannot convert {in_ext!r} → {out_fmt!r}. "
                f"Supported outputs: {supported}"
            )

        output_path = self._resolve_output_path(
            input_path, out_fmt, output_dir and Path(output_dir),
        )

        print(f"[citrus] Converting {input_path.name} → {output_path.name} …")

        # PDF page rasterisation is handled by ImageMagick/poppler rather
        # than a document office backend.
        if in_ext == "pdf" and out_fmt in {"jpg", "png"}:
            self._convert_pdf_image(input_path, output_path, out_fmt)
            return str(output_path)

        # Decide which backend to use
        use_pandoc = (
            (in_ext, out_fmt) in _PANDOC_PAIRS
            and shutil.which("pandoc")
        )

        if use_pandoc:
            self._convert_pandoc(input_path, output_path, in_ext, out_fmt)
        elif shutil.which("libreoffice"):
            self._convert_libreoffice(input_path, output_path, out_fmt)
        elif shutil.which("pandoc"):
            # Fallback to pandoc even if not the preferred pair
            self._convert_pandoc(input_path, output_path, in_ext, out_fmt)
        else:
            raise ConversionError(
                "Neither 'pandoc' nor 'libreoffice' is installed. "
                "Please install at least one."
            )

        print(f"[citrus] Done → {output_path}")
        return str(output_path)

    # ── private ──────────────────────────────────────────────────

    def _convert_pandoc(
        self,
        input_path: Path,
        output_path: Path,
        in_ext: str,
        out_fmt: str,
    ) -> None:
        """Run pandoc conversion."""
        in_fmt_name = _PANDOC_FMT.get(in_ext, in_ext)
        out_fmt_name = _PANDOC_FMT.get(out_fmt, out_fmt)

        cmd = [
            "pandoc",
            str(input_path),
            "-f", in_fmt_name,
            "-t", out_fmt_name,
            "-o", str(output_path),
            "--standalone",
        ]
        self._run_command(cmd)

    def _convert_libreoffice(
        self,
        input_path: Path,
        output_path: Path,
        out_fmt: str,
    ) -> None:
        """Run LibreOffice headless conversion.

        LibreOffice writes to a directory (it picks the filename), so we
        move the result into *output_path* afterwards.
        """
        lo_fmt = out_fmt
        # LibreOffice uses "text" for plain-text output
        if out_fmt == "txt":
            lo_fmt = "txt:Text"

        out_dir = output_path.parent

        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to", lo_fmt,
            "--outdir", str(out_dir),
            str(input_path),
        ]
        self._run_command(cmd)

        # LibreOffice names the file <stem>.<ext>
        lo_result = out_dir / f"{input_path.stem}.{out_fmt}"
        if lo_result != output_path and lo_result.exists():
            lo_result.rename(output_path)

        if not output_path.exists():
            raise ConversionError(
                f"LibreOffice did not produce the expected output file: {output_path}"
            )

    def _convert_pdf_image(self, input_path: Path, output_path: Path, out_fmt: str) -> None:
        """Render the first PDF page to an image with a local backend."""
        if shutil.which("pdftoppm"):
            import subprocess
            prefix = output_path.with_suffix("")
            self._run_command(["pdftoppm", "-singlefile", "-r", "300", "-" + out_fmt, str(input_path), str(prefix)])
            generated = prefix.with_suffix("." + out_fmt)
            if generated.exists() and generated != output_path:
                generated.rename(output_path)
            return
        if shutil.which("magick") or shutil.which("convert"):
            self._run_command([shutil.which("magick") or "convert", "-density", "300", f"{input_path}[0]", str(output_path)])
            return
        raise ConversionError("PDF image export requires pdftoppm or ImageMagick.")
