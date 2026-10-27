"""
Audio converter — uses ``ffmpeg`` as the backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseConverter, ConversionError

_AUDIO_FORMATS = ["mp3", "m4a", "wav", "flac", "ogg", "opus", "aiff", "aac", "wma"]

_CONVERSIONS = {
    fmt: [f for f in _AUDIO_FORMATS if f != fmt]
    for fmt in _AUDIO_FORMATS
}

# Default audio codecs per output format
_DEFAULT_CODECS: dict[str, str] = {
    "mp3":  "libmp3lame",
    "m4a":  "aac",
    "wav":  "pcm_s16le",
    "flac": "flac",
    "ogg":  "libvorbis",
    "opus": "libopus",
    "aiff": "pcm_s16be",
    "aac":  "aac",
    "wma":  "wmav2",
}


class AudioConverter(BaseConverter):
    """Convert between audio formats via ffmpeg."""

    _conversions = _CONVERSIONS
    _required_tools = ["ffmpeg"]

    def convert(
        self,
        input_path: str | Path,
        output_format: str,
        output_dir: str | Path | None = None,
        **options: Any,
    ) -> str:
        """Convert an audio file to *output_format*.

        Keyword options:
            bitrate (str):       e.g. ``"192k"``.
            sample_rate (int):   e.g. ``44100``.
            channels (int):      ``1`` for mono, ``2`` for stereo.

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
        if out_fmt not in supported and out_fmt not in _AUDIO_FORMATS:
            raise ConversionError(
                f"Cannot convert {in_ext!r} → {out_fmt!r}. "
                f"Supported outputs: {supported}"
            )

        output_path = self._resolve_output_path(
            input_path, out_fmt, output_dir and Path(output_dir),
        )

        print(f"[elumichai] Converting {input_path.name} → {output_path.name} …")

        codec = _DEFAULT_CODECS.get(out_fmt, "copy")

        cmd: list[str] = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-vn",                       # drop any video stream
            "-c:a", codec,
        ]

        bitrate = options.get("bitrate")
        if bitrate:
            cmd += ["-b:a", bitrate]

        sample_rate = options.get("sample_rate")
        if sample_rate:
            cmd += ["-ar", str(int(sample_rate))]

        channels = options.get("channels")
        if channels:
            cmd += ["-ac", str(int(channels))]

        cmd.append(str(output_path))
        self._run_command(cmd)

        print(f"[elumichai] Done → {output_path}")
        return str(output_path)
