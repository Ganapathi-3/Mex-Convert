"""
Audio manipulation tools — normalize, trim, channel change, info.

Uses ``ffmpeg`` and ``ffprobe``.
"""

from __future__ import annotations

import json
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


def _output_path(original: Path, suffix: str) -> Path:
    """Generate an output path next to *original*."""
    return original.parent / f"{original.stem}{suffix}{original.suffix}"


class AudioTools:
    """Collection of audio manipulation utilities backed by ffmpeg/ffprobe."""

    @staticmethod
    def normalize(path: str | Path) -> str:
        """Normalize audio loudness using the EBU R128 loudnorm filter.

        This is a two-pass process:
        1. Analyse the audio to measure loudness.
        2. Apply loudnorm filter with the measured values.

        Returns:
            Path to the normalized audio file.
        """
        path = Path(path).resolve()
        out = _output_path(path, "_normalized")
        print(f"[citrus] Normalizing {path.name} …")

        # Pass 1: measure loudness
        cmd_measure = [
            "ffmpeg", "-y", "-i", str(path),
            "-af", "loudnorm=print_format=json",
            "-f", "null", "/dev/null",
        ]
        try:
            result = subprocess.run(
                cmd_measure, capture_output=True, text=True, timeout=300,
            )
        except FileNotFoundError:
            raise ConversionError("ffmpeg not found.")

        # Parse loudnorm stats from stderr (JSON block at end)
        stderr = result.stderr
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1
        if json_start == -1 or json_end <= json_start:
            # Fallback: single-pass normalization
            cmd_simple = [
                "ffmpeg", "-y", "-i", str(path),
                "-af", "loudnorm",
                str(out),
            ]
            _run(cmd_simple)
            print(f"[citrus] Done → {out}")
            return str(out)

        stats = json.loads(stderr[json_start:json_end])

        # Pass 2: apply normalization
        loudnorm_filter = (
            f"loudnorm=I=-16:TP=-1.5:LRA=11:"
            f"measured_I={stats.get('input_i', '-24')}:"
            f"measured_TP={stats.get('input_tp', '-2')}:"
            f"measured_LRA={stats.get('input_lra', '7')}:"
            f"measured_thresh={stats.get('input_thresh', '-34')}:"
            f"offset={stats.get('target_offset', '0')}:"
            f"linear=true:print_format=summary"
        )
        cmd_apply = [
            "ffmpeg", "-y", "-i", str(path),
            "-af", loudnorm_filter,
            str(out),
        ]
        _run(cmd_apply)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def trim(path: str | Path, start: str, end: str) -> str:
        """Trim audio from *start* to *end* (HH:MM:SS or seconds).

        Returns:
            Path to the trimmed audio file.
        """
        path = Path(path).resolve()
        out = _output_path(path, "_trimmed")
        print(f"[citrus] Trimming {path.name} [{start} → {end}] …")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(path),
            "-ss", str(start),
            "-to", str(end),
            "-c", "copy",
            str(out),
        ]
        _run(cmd)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def change_channels(path: str | Path, channels: int) -> str:
        """Convert audio to *channels* channels (1 = mono, 2 = stereo, …).

        Returns:
            Path to the output audio file.
        """
        path = Path(path).resolve()
        label = "mono" if channels == 1 else f"{channels}ch"
        out = _output_path(path, f"_{label}")
        print(f"[citrus] Changing {path.name} to {channels} channel(s) …")
        cmd = [
            "ffmpeg", "-y", "-i", str(path),
            "-ac", str(int(channels)),
            str(out),
        ]
        _run(cmd)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def get_info(path: str | Path) -> dict:
        """Return audio file information via ``ffprobe``.

        Returns:
            Dict with keys: ``duration``, ``codec``, ``sample_rate``,
            ``channels``, ``bitrate``, ``format_name``.
        """
        path = Path(path).resolve()
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        _, stdout, _ = _run(cmd)
        data = json.loads(stdout)

        info: dict = {
            "path": str(path),
            "duration": data.get("format", {}).get("duration", "0"),
            "bitrate": data.get("format", {}).get("bit_rate", "0"),
            "size": data.get("format", {}).get("size", "0"),
            "format_name": data.get("format", {}).get("format_name", "unknown"),
        }

        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                info["codec"] = stream.get("codec_name", "unknown")
                info["sample_rate"] = stream.get("sample_rate", "0")
                info["channels"] = stream.get("channels", 0)
                info["channel_layout"] = stream.get("channel_layout", "unknown")
                break

        return info
