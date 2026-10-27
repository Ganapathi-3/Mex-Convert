"""
Video converter — uses ``ffmpeg`` as the backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseConverter, ConversionError

_VIDEO_FORMATS = ["mp4", "mov", "mkv", "avi", "wmv", "webm", "gif", "mp3"]

_CONVERSIONS = {
    fmt: [f for f in _VIDEO_FORMATS if f != fmt]
    for fmt in _VIDEO_FORMATS
}

# Sensible default codecs per container
_DEFAULT_CODECS: dict[str, dict[str, str]] = {
    "mp4":  {"vcodec": "libx264",  "acodec": "aac"},
    "mov":  {"vcodec": "libx264",  "acodec": "aac"},
    "mkv":  {"vcodec": "libx264",  "acodec": "aac"},
    "avi":  {"vcodec": "mpeg4",    "acodec": "mp3"},
    "wmv":  {"vcodec": "wmv2",     "acodec": "wmav2"},
    "webm": {"vcodec": "libvpx-vp9", "acodec": "libopus"},
    "gif":  {"vcodec": "gif",      "acodec": ""},
}


class VideoConverter(BaseConverter):
    """Convert between video container/codec formats via ffmpeg."""

    _conversions = _CONVERSIONS
    _required_tools = ["ffmpeg"]

    def convert(
        self,
        input_path: str | Path,
        output_format: str,
        output_dir: str | Path | None = None,
        **options: Any,
    ) -> str:
        """Convert a video file to *output_format*.

        Keyword options:
            resolution (str):  e.g. ``"1280x720"``
            bitrate (str):     e.g. ``"2M"``
            fps (int|float):   Frames per second.
            codec (str):       Video codec override (e.g. ``"libx265"``).

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
        if out_fmt not in supported and out_fmt not in _VIDEO_FORMATS:
            raise ConversionError(
                f"Cannot convert {in_ext!r} → {out_fmt!r}. "
                f"Supported outputs: {supported}"
            )

        output_path = self._resolve_output_path(
            input_path, out_fmt, output_dir and Path(output_dir),
        )

        print(f"[elumichai] Converting {input_path.name} → {output_path.name} …")

        # Tangerine exposes MP3 extraction directly from the video wheel.
        if out_fmt == "mp3":
            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vn", "-c:a", "libmp3lame", str(output_path),
            ]
            bitrate = options.get("bitrate")
            if bitrate:
                cmd[-1:-1] = ["-b:a", str(bitrate)]
            self._run_command(cmd)
            return str(output_path)

        defaults = _DEFAULT_CODECS.get(out_fmt, {"vcodec": "copy", "acodec": "copy"})

        cmd: list[str] = ["ffmpeg", "-y", "-i", str(input_path)]

        # Video codec
        vcodec = options.get("codec", defaults["vcodec"])
        cmd += ["-c:v", vcodec]

        # Audio codec (skip for GIF)
        if out_fmt == "gif":
            cmd += ["-an"]
        else:
            cmd += ["-c:a", defaults["acodec"]]

        # Optional: resolution
        resolution = options.get("resolution")
        if resolution:
            cmd += ["-s", resolution]

        # Optional: bitrate
        bitrate = options.get("bitrate")
        if bitrate:
            cmd += ["-b:v", bitrate]

        # Optional: fps
        fps = options.get("fps")
        if fps:
            cmd += ["-r", str(fps)]

        cmd.append(str(output_path))
        self._run_command(cmd)

        print(f"[elumichai] Done → {output_path}")
        return str(output_path)
