"""Tools package — re-exports every tool class and provides
a ``get_tool()`` factory function for convenience."""

from __future__ import annotations

from typing import Optional

from .audio_tools import AudioTools
from .image_tools import ImageTools
from .metadata import MetadataTools
from .pdf_tools import PdfTools
from .video_tools import VideoTools

__all__ = [
    "ImageTools",
    "VideoTools",
    "AudioTools",
    "PdfTools",
    "MetadataTools",
    "get_tool",
]

# Category → tool instance cache (lazy)
_TOOLS: dict[str, object] = {}


def get_tool(category: str | None) -> object | None:
    """Return the appropriate tool class instance for *category*.

    Args:
        category: One of ``'image'``, ``'video'``, ``'audio'``,
                  ``'document'``.

    Returns:
        A tool instance, or ``None`` if the category is unknown / has no tools.
    """
    if not category:
        return None

    category = category.lower()

    if category not in _TOOLS:
        cls_map: dict[str, type] = {
            "image":    ImageTools,
            "video":    VideoTools,
            "audio":    AudioTools,
            "document": PdfTools,
            "slide": PdfTools,
            "spreadsheet": PdfTools,
            "subtitle": MetadataTools,
        }
        cls = cls_map.get(category)
        if cls is None:
            return None
        _TOOLS[category] = cls()

    return _TOOLS[category]
