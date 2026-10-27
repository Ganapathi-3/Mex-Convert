"""Converters package — re-exports every converter class and provides
a ``get_converter()`` factory function for convenience."""

from __future__ import annotations

from typing import Optional

from .archive import ArchiveConverter
from .audio import AudioConverter
from .base import BaseConverter, ConversionError
from .document import DocumentConverter
from .image import ImageConverter
from .video import VideoConverter

__all__ = [
    "BaseConverter",
    "ConversionError",
    "ImageConverter",
    "VideoConverter",
    "AudioConverter",
    "DocumentConverter",
    "ArchiveConverter",
    "get_converter",
]

# Category → converter instance cache (lazy)
_CONVERTERS: dict[str, BaseConverter] = {}


def get_converter(category: str | None) -> BaseConverter | None:
    """Return the appropriate converter for *category*.

    Args:
        category: One of ``'image'``, ``'video'``, ``'audio'``,
                  ``'document'``, ``'archive'``.

    Returns:
        A converter instance, or ``None`` if the category is unknown.
    """
    if not category:
        return None

    category = category.lower()

    if category not in _CONVERTERS:
        cls_map: dict[str, type[BaseConverter]] = {
            "image":    ImageConverter,
            "video":    VideoConverter,
            "audio":    AudioConverter,
            "document": DocumentConverter,
            "slide":    DocumentConverter,
            "spreadsheet": DocumentConverter,
            "subtitle": DocumentConverter,
            "archive":  ArchiveConverter,
        }
        cls = cls_map.get(category)
        if cls is None:
            return None
        _CONVERTERS[category] = cls()

    return _CONVERTERS[category]
