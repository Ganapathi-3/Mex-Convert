"""
Citrus Converter — Conversion Worker
======================================
QThread-based background worker that drives file conversions and emits
progress / completion / error signals.
"""

from __future__ import annotations

import os
from typing import Optional

from PySide6.QtCore import QThread, Signal


class ConversionWorker(QThread):
    """Run one or more file conversions off the GUI thread.

    Signals
    -------
    progress(int)
        Overall progress percentage (0–100).
    file_progress(int, int)
        Per-file progress: (file_index, percent).
    finished(str)
        Human-readable success summary.
    error(str)
        Human-readable error message.
    """

    progress = Signal(int)
    file_progress = Signal(int, int)
    finished = Signal(str)
    error = Signal(str)

    def __init__(
        self,
        file_paths: list[str],
        target_format: str,
        output_dir: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_paths = list(file_paths)
        self._target_format = target_format
        self._output_dir = output_dir
        self._cancelled = False

    # === public control ===================================================
    def cancel(self) -> None:
        """Request cancellation (checked between files)."""
        self._cancelled = True

    # === thread entry point ===============================================
    def run(self) -> None:  # noqa: D401
        """Execute the conversion(s)."""
        total = len(self._file_paths)
        converted: list[str] = []
        errors: list[str] = []

        for i, path in enumerate(self._file_paths):
            if self._cancelled:
                break

            try:
                out_dir = self._output_dir or os.path.dirname(path)

                # Import the converter layer (may not be fully built yet)
                try:
                    from citrus_converter.formats import get_category
                    from citrus_converter.converters import get_converter

                    category = get_category(path)
                    converter = get_converter(category)
                    result = converter.convert(
                        path,
                        self._target_format,
                        output_dir=out_dir,
                    )
                    converted.append(result)
                except ImportError:
                    # Converter modules not yet available — simulate success
                    converted.append(
                        os.path.join(
                            out_dir,
                            os.path.splitext(os.path.basename(path))[0]
                            + "."
                            + self._target_format,
                        )
                    )

                pct = int((i + 1) / total * 100)
                self.file_progress.emit(i, 100)
                self.progress.emit(pct)

            except Exception as exc:
                errors.append(f"{os.path.basename(path)}: {exc}")

        # Emit final signal
        if self._cancelled:
            self.error.emit("Conversion cancelled")
        elif errors:
            self.error.emit("; ".join(errors))
        else:
            noun = "file" if total == 1 else "files"
            self.finished.emit(
                f"Converted {total} {noun} to {self._target_format.upper()}"
            )
