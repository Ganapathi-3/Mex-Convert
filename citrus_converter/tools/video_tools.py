"""
Video manipulation tools — compress, trim, extract audio, snapshot, speed, info.

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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        raise ConversionError(f"Command not found: {cmd[0]!r}")
    if result.returncode != 0:
        raise ConversionError(
            f"Command failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result.returncode, result.stdout, result.stderr


def _output_path(original: Path, suffix: str, ext: str | None = None) -> Path:
    """Generate an output path next to *original*."""
    extension = ext or original.suffix
    return original.parent / f"{original.stem}{suffix}{extension}"


class VideoTools:
    """Collection of video manipulation utilities backed by ffmpeg/ffprobe."""

    @staticmethod
    def compress(
        path: str | Path,
        target_size_mb: float | None = None,
        crf: int = 28,
    ) -> str:
        """Compress a video using CRF or targeting a specific file size.

        Args:
            path: Input video file.
            target_size_mb: Desired output size in MB.  If given, the
                bitrate is calculated automatically (overrides *crf*).
            crf: Constant Rate Factor (0-51, lower = better quality).

        Returns:
            Path to the compressed video.
        """
        path = Path(path).resolve()
        out = _output_path(path, "_compressed")
        print(f"[citrus] Compressing {path.name} …")

        if target_size_mb is not None:
            # Calculate bitrate from target size and duration
            info = VideoTools.get_info(str(path))
            duration = float(info.get("duration", 0))
            if duration <= 0:
                raise ConversionError("Cannot determine video duration for size targeting.")
            # target bits = target_size_mb * 8 * 1024 * 1024; bitrate = bits / duration
            target_bitrate = int((target_size_mb * 8 * 1024 * 1024) / duration)
            cmd = [
                "ffmpeg", "-y", "-i", str(path),
                "-c:v", "libx264", "-b:v", str(target_bitrate),
                "-c:a", "aac", "-b:a", "128k",
                str(out),
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", str(path),
                "-c:v", "libx264", "-crf", str(crf),
                "-c:a", "aac",
                str(out),
            ]
        _run(cmd)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def trim(path: str | Path, start: str, end: str) -> str:
        """Trim a video from *start* to *end* (HH:MM:SS or seconds).

        Returns:
            Path to the trimmed video.
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
    def extract_audio(path: str | Path, format: str = "mp3") -> str:
        """Extract the audio track from a video.

        Args:
            path: Input video file.
            format: Output audio format (default ``mp3``).

        Returns:
            Path to the extracted audio file.
        """
        path = Path(path).resolve()
        fmt = format.lower().lstrip(".")
        out = _output_path(path, "_audio", f".{fmt}")
        print(f"[citrus] Extracting audio from {path.name} → .{fmt} …")

        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "m4a": "aac",
            "wav": "pcm_s16le",
            "flac": "flac",
            "ogg": "libvorbis",
            "opus": "libopus",
        }
        codec = codec_map.get(fmt, "copy")

        cmd = [
            "ffmpeg", "-y", "-i", str(path),
            "-vn", "-c:a", codec,
            str(out),
        ]
        _run(cmd)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def snapshot(path: str | Path, timestamp: str) -> str:
        """Capture a single frame at *timestamp* (HH:MM:SS or seconds).

        Returns:
            Path to the PNG snapshot.
        """
        path = Path(path).resolve()
        out = _output_path(path, f"_snap_{timestamp.replace(':', '')}", ".png")
        print(f"[citrus] Taking snapshot of {path.name} at {timestamp} …")
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", str(path),
            "-frames:v", "1",
            str(out),
        ]
        _run(cmd)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def change_speed(path: str | Path, factor: float) -> str:
        """Change playback speed by *factor* (e.g. ``2.0`` = 2× faster).

        Returns:
            Path to the speed-adjusted video.
        """
        path = Path(path).resolve()
        label = f"{factor}x".replace(".", "_")
        out = _output_path(path, f"_{label}")
        print(f"[citrus] Changing speed of {path.name} → {factor}× …")

        # Video: setpts=PTS/factor; Audio: atempo=factor (atempo range 0.5-2.0)
        video_filter = f"setpts=PTS/{factor}"

        # Chain atempo filters for factors outside 0.5-2.0
        atempo_filters: list[str] = []
        remaining = factor
        while remaining > 2.0:
            atempo_filters.append("atempo=2.0")
            remaining /= 2.0
        while remaining < 0.5:
            atempo_filters.append("atempo=0.5")
            remaining /= 0.5
        atempo_filters.append(f"atempo={remaining}")
        audio_filter = ",".join(atempo_filters)

        cmd = [
            "ffmpeg", "-y", "-i", str(path),
            "-filter:v", video_filter,
            "-filter:a", audio_filter,
            str(out),
        ]
        _run(cmd)
        print(f"[citrus] Done → {out}")
        return str(out)

    @staticmethod
    def get_info(path: str | Path) -> dict:
        """Return video file information via ``ffprobe``.

        Returns:
            Dict with keys like ``duration``, ``width``, ``height``,
            ``codec``, ``fps``, ``bitrate``, ``audio_codec``, etc.
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
            if stream.get("codec_type") == "video":
                info["width"] = stream.get("width", 0)
                info["height"] = stream.get("height", 0)
                info["codec"] = stream.get("codec_name", "unknown")
                fps_str = stream.get("r_frame_rate", "0/1")
                try:
                    num, den = fps_str.split("/")
                    info["fps"] = round(int(num) / int(den), 2) if int(den) else 0
                except (ValueError, ZeroDivisionError):
                    info["fps"] = 0
            elif stream.get("codec_type") == "audio":
                info["audio_codec"] = stream.get("codec_name", "unknown")
                info["audio_sample_rate"] = stream.get("sample_rate", "0")
                info["audio_channels"] = stream.get("channels", 0)

        return info
