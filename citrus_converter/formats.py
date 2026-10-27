"""
Format registry for Elumichai.

Centralised mapping of file extensions to categories, converter classes,
supported conversions, and format metadata (display name, extension, MIME type).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


# ── Format metadata ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FormatInfo:
    """Metadata for a single file format."""

    display_name: str
    extension: str          # canonical extension, without the dot
    mime_type: str
    category: str           # image | video | audio | document | ...


# Complete registry keyed by canonical lower-case extension.
FORMAT_REGISTRY: Dict[str, FormatInfo] = {
    # ── Images ───────────────────────────────────────────────────
    "jpeg": FormatInfo("JPEG Image",          "jpeg", "image/jpeg",               "image"),
    "jpg":  FormatInfo("JPEG Image",          "jpg",  "image/jpeg",               "image"),
    "png":  FormatInfo("PNG Image",           "png",  "image/png",                "image"),
    "heic": FormatInfo("HEIC Image",          "heic", "image/heic",               "image"),
    "webp": FormatInfo("WebP Image",          "webp", "image/webp",               "image"),
    "tiff": FormatInfo("TIFF Image",          "tiff", "image/tiff",               "image"),
    "tif":  FormatInfo("TIFF Image",          "tif",  "image/tiff",               "image"),
    "bmp":  FormatInfo("BMP Image",           "bmp",  "image/bmp",                "image"),
    "svg":  FormatInfo("SVG Image",           "svg",  "image/svg+xml",            "image"),
    "gif":  FormatInfo("GIF Image",           "gif",  "image/gif",                "image"),
    "avif": FormatInfo("AVIF Image",          "avif", "image/avif",               "image"),
    "ico":  FormatInfo("ICO Icon",            "ico",  "image/x-icon",             "image"),

    # ── Video ────────────────────────────────────────────────────
    "mp4":  FormatInfo("MP4 Video",           "mp4",  "video/mp4",                "video"),
    "mov":  FormatInfo("QuickTime Video",     "mov",  "video/quicktime",          "video"),
    "mkv":  FormatInfo("Matroska Video",      "mkv",  "video/x-matroska",         "video"),
    "avi":  FormatInfo("AVI Video",           "avi",  "video/x-msvideo",          "video"),
    "wmv":  FormatInfo("WMV Video",           "wmv",  "video/x-ms-wmv",           "video"),
    "webm": FormatInfo("WebM Video",          "webm", "video/webm",               "video"),

    # ── Audio ────────────────────────────────────────────────────
    "mp3":  FormatInfo("MP3 Audio",           "mp3",  "audio/mpeg",               "audio"),
    "m4a":  FormatInfo("M4A Audio",           "m4a",  "audio/mp4",                "audio"),
    "wav":  FormatInfo("WAV Audio",           "wav",  "audio/wav",                "audio"),
    "flac": FormatInfo("FLAC Audio",          "flac", "audio/flac",               "audio"),
    "ogg":  FormatInfo("OGG Audio",           "ogg",  "audio/ogg",                "audio"),
    "opus": FormatInfo("Opus Audio",          "opus", "audio/opus",               "audio"),
    "aiff": FormatInfo("AIFF Audio",          "aiff", "audio/aiff",               "audio"),
    "aac":  FormatInfo("AAC Audio",           "aac",  "audio/aac",                "audio"),
    "wma":  FormatInfo("WMA Audio",           "wma",  "audio/x-ms-wma",           "audio"),

    # ── Documents ────────────────────────────────────────────────
    "pdf":  FormatInfo("PDF Document",        "pdf",  "application/pdf",          "document"),
    "txt":  FormatInfo("Plain Text",          "txt",  "text/plain",               "document"),
    "docx": FormatInfo("Word Document",       "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "document"),
    "odt":  FormatInfo("OpenDocument Text",   "odt",  "application/vnd.oasis.opendocument.text", "document"),
    "rtf":  FormatInfo("Rich Text Format",    "rtf",  "application/rtf",          "document"),
    "html": FormatInfo("HTML Document",       "html", "text/html",                "document"),
    "md":   FormatInfo("Markdown Document",   "md",   "text/markdown",            "document"),
    "epub": FormatInfo("EPUB E-Book",         "epub", "application/epub+zip",     "document"),
    "pages": FormatInfo("Pages Document",     "pages", "application/x-iwork-pages-sffpages", "document"),
    "rtfd": FormatInfo("Rich Text Directory", "rtfd", "application/rtf",          "document"),
    "clipping": FormatInfo("Text Clipping",   "clipping", "text/plain",           "document"),

    # Presentations and spreadsheets use the same local office backends but
    # remain separate families in the conversion wheel.
    "ppt":  FormatInfo("PowerPoint Presentation", "ppt", "application/vnd.ms-powerpoint", "slide"),
    "pptx": FormatInfo("PowerPoint Presentation", "pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "slide"),
    "xlsx": FormatInfo("Excel Spreadsheet", "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "spreadsheet"),
    "xls":  FormatInfo("Excel Spreadsheet", "xls", "application/vnd.ms-excel", "spreadsheet"),
    "ods":  FormatInfo("OpenDocument Spreadsheet", "ods", "application/vnd.oasis.opendocument.spreadsheet", "spreadsheet"),
    "csv":  FormatInfo("CSV Spreadsheet", "csv", "text/csv", "spreadsheet"),
    "tsv":  FormatInfo("TSV Spreadsheet", "tsv", "text/tab-separated-values", "spreadsheet"),
    "srt":  FormatInfo("SubRip Subtitle", "srt", "application/x-subrip", "subtitle"),
    "vtt":  FormatInfo("WebVTT Subtitle", "vtt", "text/vtt", "subtitle"),

    # ── Archives ─────────────────────────────────────────────────
    "zip":     FormatInfo("ZIP Archive",      "zip",     "application/zip",       "archive"),
    "tar":     FormatInfo("TAR Archive",      "tar",     "application/x-tar",     "archive"),
    "tar.gz":  FormatInfo("Gzipped TAR",      "tar.gz",  "application/gzip",      "archive"),
    "tar.bz2": FormatInfo("Bzip2 TAR",        "tar.bz2", "application/x-bzip2",   "archive"),
    "tar.xz":  FormatInfo("XZ TAR",           "tar.xz",  "application/x-xz",      "archive"),
    "gz":      FormatInfo("GZIP Archive",     "gz",      "application/gzip",      "archive"),
    "gzip":    FormatInfo("GZIP Archive",     "gzip",    "application/gzip",      "archive"),
    "rar":     FormatInfo("RAR Archive",      "rar",     "application/vnd.rar",   "archive"),
    "7z":      FormatInfo("7-Zip Archive",    "7z",      "application/x-7z-compressed", "archive"),
}


# ── Category metadata ───────────────────────────────────────────────────────

CATEGORY_MAP: Dict[str, dict] = {
    "image":    {"name": "Images",    "description": "Raster and vector image formats"},
    "video":    {"name": "Video",     "description": "Video container formats"},
    "audio":    {"name": "Audio",     "description": "Audio file formats"},
    "document": {"name": "Documents", "description": "Text and document formats"},
    "slide":   {"name": "Slides",    "description": "Presentation formats"},
    "spreadsheet": {"name": "Spreadsheets", "description": "Tabular data formats"},
    "subtitle": {"name": "Subtitles", "description": "Timed text formats"},
    "archive":  {"name": "Archives",  "description": "Compressed archive formats"},
}

# ── Category → converter class name ─────────────────────────────────────────

CATEGORY_CONVERTER: Dict[str, str] = {
    "image":    "ImageConverter",
    "video":    "VideoConverter",
    "audio":    "AudioConverter",
    "document": "DocumentConverter",
    "slide":    "DocumentConverter",
    "spreadsheet": "DocumentConverter",
    "subtitle": "DocumentConverter",
    "archive":  "ArchiveConverter",
}


# ── Supported conversions (input ext → list of output exts) ─────────────────

IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp", "heic", "tiff", "tif", "avif", "bmp", "gif", "ico", "svg"]
VIDEO_FORMATS = ["mp4", "mov", "mkv", "webm", "avi", "wmv", "gif"]
AUDIO_FORMATS = ["mp3", "m4a", "wav", "flac", "ogg", "opus", "aiff", "wma", "aac"]
DOCUMENT_FORMATS = ["pdf", "docx", "pages", "md", "txt", "epub", "rtf", "rtfd", "clipping", "html", "odt"]
SLIDE_FORMATS = ["ppt", "pptx", "pdf"]
SPREADSHEET_FORMATS = ["xlsx", "ods", "csv", "tsv", "xls", "pdf"]
SUBTITLE_FORMATS = ["srt", "vtt", "txt"]
ARCHIVE_FORMATS = ["zip", "tar", "gz", "gzip", "rar"]


def _build_conversion_map(formats: List[str]) -> Dict[str, List[str]]:
    """Each format can convert to every other format in the same group."""
    return {fmt: [f for f in formats if f != fmt] for fmt in formats}


CONVERSION_MAP: Dict[str, List[str]] = {
    **{fmt: [f for f in IMAGE_FORMATS if f != fmt] + (["pdf"] if fmt != "svg" else [])
       for fmt in IMAGE_FORMATS},
    **{fmt: [f for f in VIDEO_FORMATS if f != fmt] + ["mp3"] for fmt in VIDEO_FORMATS},
    **_build_conversion_map(AUDIO_FORMATS),
    "pdf": ["docx", "pages", "pptx", "xlsx", "jpg", "png", "epub", "txt", "md"],
    "docx": ["pdf", "pages", "md", "txt", "epub", "html"],
    "pages": ["pdf", "docx", "md", "txt", "epub", "html"],
    "md": ["pdf", "docx", "pages", "txt", "epub", "html"],
    "txt": ["pdf", "docx", "pages", "md", "epub", "html"],
    "epub": ["pdf", "docx", "pages", "md", "txt", "html"],
    "rtf": ["pdf", "docx", "md", "txt", "epub", "html"],
    "rtfd": ["pdf", "docx", "md", "txt", "epub", "html"],
    "clipping": ["pdf", "docx", "md", "txt", "epub", "html"],
    "html": ["pdf", "docx", "md", "txt", "epub"],
    "odt": ["pdf", "docx", "md", "txt", "epub", "html"],
    "ppt": ["pdf", "jpg", "png"],
    "pptx": ["pdf", "jpg", "png"],
    "xlsx": ["pdf", "ods", "csv", "tsv"],
    "ods": ["pdf", "xlsx", "csv", "tsv"],
    "csv": ["pdf", "xlsx", "ods", "tsv"],
    "tsv": ["pdf", "xlsx", "ods", "csv"],
    "xls": ["pdf", "xlsx", "ods", "csv", "tsv"],
    "srt": ["vtt", "txt"],
    "vtt": ["srt", "txt"],
    "zip": ["tar", "gz"],
    "tar": ["zip", "gz"],
    "gz": ["zip", "tar"],
    "gzip": ["zip", "tar"],
    "rar": ["zip", "tar", "gz"],
    "7z": ["zip", "tar", "gz"],
    "tar.gz": ["zip", "tar", "gz"],
    "tar.bz2": ["zip", "tar", "gz"],
    "tar.xz": ["zip", "tar", "gz"],
}

# ── Tools available per category ────────────────────────────────────────────

CATEGORY_TOOLS: Dict[str, List[str]] = {
    "image": ["compress", "edit_metadata", "edit_photos", "annotate_photos", "add_background", "crop_images", "redact_photos", "create_pdf", "create_collage"],
    "video": ["compress", "trim_video", "crop_video", "change_video_speed", "join_videos", "save_video_frames", "split_video", "redact_video"],
    "audio": ["normalize_volume", "create_audio_visualizer", "trim_audio", "convert_audio_channels", "bleep_audio"],
    "document": ["compress", "edit_metadata", "merge_pdfs", "organize_pdf_pages"],
    "slide": ["compress", "edit_metadata"],
    "spreadsheet": ["compress", "edit_metadata"],
    "subtitle": ["compress", "edit_metadata"],
    "archive": ["compress", "edit_metadata"],
}


# ── Helper look-ups ─────────────────────────────────────────────────────────


def _file_extension(path: str) -> str:
    """Extract the compound extension from a file path (handles tar.gz etc)."""
    name = os.path.basename(path).lower()
    for compound in ("tar.gz", "tar.bz2", "tar.xz"):
        if name.endswith(f".{compound}"):
            return compound
    _, ext = os.path.splitext(name)
    return ext.lstrip(".")


def extension_to_category(ext: str) -> str | None:
    """Return the category (image, video, …) for a file extension, or None."""
    ext = ext.lower().lstrip(".")
    info = FORMAT_REGISTRY.get(ext)
    return info.category if info else None


def get_format_info(ext: str) -> FormatInfo | None:
    """Return :class:`FormatInfo` for an extension, or None."""
    return FORMAT_REGISTRY.get(ext.lower().lstrip("."))


def get_supported_outputs(input_ext: str) -> List[str]:
    """Return list of valid output extensions for *input_ext*."""
    return CONVERSION_MAP.get(input_ext.lower().lstrip("."), [])


def get_category(file_path: str) -> str | None:
    """Return the category for a file given its path, or None if unsupported."""
    ext = _file_extension(file_path)
    return extension_to_category(ext)


def get_conversions_for_file(file_path: str) -> List[str]:
    """Return list of output formats a file can be converted to."""
    ext = _file_extension(file_path)
    return get_supported_outputs(ext)


def get_tools_for_file(file_path: str) -> List[str]:
    """Return list of tool names available for a file's category."""
    category = get_category(file_path)
    if not category:
        return []
    return list(CATEGORY_TOOLS.get(category, []))
