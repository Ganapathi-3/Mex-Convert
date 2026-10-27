"""
PDF tools — merge, split, and inspect PDF files.

Uses ``qpdf`` as the primary backend with ``gs`` (Ghostscript) as fallback.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from citrus_converter.converters.base import ConversionError


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


class PdfTools:
    """PDF manipulation utilities (merge, split, info).

    Backend priority: ``qpdf`` → ``gs`` (Ghostscript).
    """

    # ── merge ────────────────────────────────────────────────────

    @staticmethod
    def merge(paths: list[str | Path], output: str | Path) -> str:
        """Merge multiple PDF files into one.

        Args:
            paths: List of input PDF file paths (in order).
            output: Destination file path.

        Returns:
            Absolute path of the merged PDF.
        """
        if not paths:
            raise ConversionError("No input files provided for merge.")
        resolved = [str(Path(p).resolve()) for p in paths]
        output = Path(output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        print(f"[citrus] Merging {len(resolved)} PDFs → {output.name} …")

        if shutil.which("qpdf"):
            PdfTools._merge_qpdf(resolved, output)
        elif shutil.which("gs"):
            PdfTools._merge_gs(resolved, output)
        else:
            raise ConversionError(
                "Neither 'qpdf' nor 'gs' (Ghostscript) is installed. "
                "Please install one to merge PDFs."
            )

        print(f"[citrus] Done → {output}")
        return str(output)

    @staticmethod
    def _merge_qpdf(inputs: list[str], output: Path) -> None:
        """Merge with qpdf."""
        cmd = ["qpdf", "--empty", "--pages"] + inputs + ["--", str(output)]
        _run(cmd)

    @staticmethod
    def _merge_gs(inputs: list[str], output: Path) -> None:
        """Merge with Ghostscript."""
        cmd = [
            "gs", "-dBATCH", "-dNOPAUSE", "-q",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={output}",
        ] + inputs
        _run(cmd)

    # ── split ────────────────────────────────────────────────────

    @staticmethod
    def split(path: str | Path, output_dir: str | Path) -> list[str]:
        """Split a PDF into individual pages.

        Args:
            path: Input PDF file.
            output_dir: Directory to write per-page PDFs.

        Returns:
            List of paths to the individual page files.
        """
        path = Path(path).resolve()
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[citrus] Splitting {path.name} into pages → {output_dir} …")

        if shutil.which("qpdf"):
            pages = PdfTools._split_qpdf(path, output_dir)
        elif shutil.which("gs"):
            pages = PdfTools._split_gs(path, output_dir)
        else:
            raise ConversionError(
                "Neither 'qpdf' nor 'gs' (Ghostscript) is installed. "
                "Please install one to split PDFs."
            )

        print(f"[citrus] Done — {len(pages)} page(s) extracted.")
        return pages

    @staticmethod
    def _split_qpdf(path: Path, output_dir: Path) -> list[str]:
        """Split with qpdf."""
        # First, determine number of pages
        _, stdout, _ = _run(["qpdf", "--show-npages", str(path)])
        num_pages = int(stdout.strip())

        pages: list[str] = []
        for i in range(1, num_pages + 1):
            out = output_dir / f"{path.stem}_page{i}.pdf"
            _run([
                "qpdf", str(path),
                "--pages", str(path), str(i), "--",
                str(out),
            ])
            pages.append(str(out))
        return pages

    @staticmethod
    def _split_gs(path: Path, output_dir: Path) -> list[str]:
        """Split with Ghostscript — writes ``<stem>_page%d.pdf``."""
        pattern = str(output_dir / f"{path.stem}_page%d.pdf")
        _run([
            "gs", "-dBATCH", "-dNOPAUSE", "-q",
            "-sDEVICE=pdfwrite",
            f"-sOutputFile={pattern}",
            str(path),
        ])
        # Collect generated files
        pages = sorted(output_dir.glob(f"{path.stem}_page*.pdf"))
        return [str(p) for p in pages]

    # ── info ─────────────────────────────────────────────────────

    @staticmethod
    def get_info(path: str | Path) -> dict:
        """Return basic PDF metadata (page count, title, author, …).

        Uses ``qpdf --show-npages`` and ``qpdf --show-object`` or
        Ghostscript as a fallback.

        Returns:
            Dict with keys: ``path``, ``pages``, ``title``, ``author``,
            ``encrypted``.
        """
        path = Path(path).resolve()
        info: dict = {"path": str(path)}

        if shutil.which("qpdf"):
            # Page count
            try:
                _, stdout, _ = _run(["qpdf", "--show-npages", str(path)])
                info["pages"] = int(stdout.strip())
            except (ConversionError, ValueError):
                info["pages"] = -1

            # Encryption check
            result = subprocess.run(
                ["qpdf", "--is-encrypted", str(path)],
                capture_output=True, text=True,
            )
            info["encrypted"] = result.returncode == 0

        elif shutil.which("gs"):
            # Use gs to count pages (write to stdout and count)
            try:
                result = subprocess.run(
                    [
                        "gs", "-dBATCH", "-dNOPAUSE", "-q",
                        "-dNODISPLAY",
                        "-c", f"({path}) (r) file runpdfbegin pdfpagecount = quit",
                    ],
                    capture_output=True, text=True, timeout=30,
                )
                info["pages"] = int(result.stdout.strip())
            except (ValueError, subprocess.TimeoutExpired):
                info["pages"] = -1
        else:
            info["pages"] = -1
            info["note"] = "Install qpdf or gs for full PDF info."

        return info
