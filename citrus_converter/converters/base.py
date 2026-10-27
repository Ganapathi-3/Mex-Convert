"""
Base converter providing the interface and common utilities for all converters.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


class ConversionError(Exception):
    """Raised when a file conversion fails."""


class BaseConverter:
    """Abstract base class for all Elumichai converters.

    Subclasses must populate ``_conversions`` — a dict mapping each supported
    input extension (lower-case, no dot) to a list of valid output extensions.
    """

    # Subclasses override: {"png": ["jpeg", "webp", …], …}
    _conversions: dict[str, list[str]] = {}

    # External tools required (checked at instantiation)
    _required_tools: list[str] = []

    def __init__(self) -> None:
        self._check_tools()

    # ── public API ───────────────────────────────────────────────

    def get_supported_conversions(self, input_format: str) -> list[str]:
        """Return the list of output formats available for *input_format*.

        Args:
            input_format: File extension (with or without leading dot).

        Returns:
            List of output extensions (lower-case, no dot).
        """
        key = input_format.lower().lstrip(".")
        return list(self._conversions.get(key, []))

    def convert(
        self,
        input_path: str | Path,
        output_format: str,
        output_dir: str | Path | None = None,
        **options: Any,
    ) -> str:
        """Convert *input_path* to *output_format*.

        Args:
            input_path: Source file.
            output_format: Desired output extension (no dot).
            output_dir: Directory for the result.  Defaults to the same
                        directory as *input_path*.
            **options: Converter-specific options (quality, bitrate, …).

        Returns:
            Absolute path of the newly created file.

        Raises:
            ConversionError: On any conversion failure.
            FileNotFoundError: If *input_path* does not exist.
        """
        raise NotImplementedError("Subclasses must implement convert()")

    # ── helpers ──────────────────────────────────────────────────

    def _resolve_output_path(
        self,
        input_path: Path,
        output_format: str,
        output_dir: Path | None = None,
    ) -> Path:
        """Build an output path, avoiding overwrites by appending a counter."""
        fmt = output_format.lower().lstrip(".")
        parent = Path(output_dir) if output_dir else input_path.parent
        parent.mkdir(parents=True, exist_ok=True)
        base = input_path.stem
        candidate = parent / f"{base}.{fmt}"
        counter = 1
        while candidate.exists():
            candidate = parent / f"{base}_{counter}.{fmt}"
            counter += 1
        return candidate

    def _run_command(self, cmd: list[str]) -> tuple[int, str, str]:
        """Execute *cmd* via :func:`subprocess.run` and return
        ``(returncode, stdout, stderr)``.

        Raises:
            ConversionError: If the process returns a non-zero exit code.
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute safety net
            )
        except FileNotFoundError:
            raise ConversionError(
                f"Command not found: {cmd[0]!r}. "
                "Please make sure the required tool is installed."
            )
        except subprocess.TimeoutExpired:
            raise ConversionError(
                f"Command timed out after 600 s: {' '.join(cmd)}"
            )

        if result.returncode != 0:
            raise ConversionError(
                f"Command failed (exit {result.returncode}):\n"
                f"  cmd: {' '.join(cmd)}\n"
                f"  stderr: {result.stderr.strip()}"
            )
        return result.returncode, result.stdout, result.stderr

    def _check_tools(self) -> None:
        """Warn (but don't crash) if required CLI tools are missing."""
        for tool in self._required_tools:
            if shutil.which(tool) is None:
                print(
                    f"[elumichai] WARNING: '{tool}' not found on PATH. "
                    f"Some conversions may fail."
                )

    @staticmethod
    def _validate_input(input_path: Path) -> None:
        """Raise if *input_path* does not exist or is not a file."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        if not input_path.is_file():
            raise ConversionError(f"Input path is not a file: {input_path}")
