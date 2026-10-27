#!/usr/bin/env python3
"""
Elumichai — Command-Line Interface

Usage:
    elumichai-cli convert <input_file> <output_format> [--output-dir DIR] [--quality Q]
    elumichai-cli info <file>
    elumichai-cli formats [<file_or_category>]
    elumichai-cli tools <tool_name> <file> [options...]
    elumichai-cli batch <input_dir> <output_format> [--output-dir DIR] [--recursive]
    elumichai-cli check-deps

Examples:
    elumichai-cli convert photo.heic png
    elumichai-cli convert video.mkv mp4 --output-dir /tmp
    elumichai-cli info photo.jpg
    elumichai-cli formats image
    elumichai-cli tools compress photo.jpg --quality 80
    elumichai-cli tools trim video.mp4 --start 00:01:00 --end 00:02:30
    elumichai-cli batch ./photos/ webp --recursive
    elumichai-cli check-deps
"""

import argparse
import sys
import os
from pathlib import Path

from citrus_converter import __version__, __app_name__
from citrus_converter.formats import (
    get_category,
    get_conversions_for_file,
    get_tools_for_file,
    CATEGORY_MAP,
    FORMAT_REGISTRY,
)
from citrus_converter.converters import get_converter
from citrus_converter.tools import get_tool


def cmd_convert(args):
    """Convert a file to another format."""
    input_path = Path(args.input_file).resolve()
    if not input_path.exists():
        print(f" Error: File not found: {input_path}")
        return 1

    category = get_category(str(input_path))
    if not category:
        print(f" Error: Unsupported file type: {input_path.suffix}")
        return 1

    available = get_conversions_for_file(str(input_path))
    target = args.output_format.lower().lstrip(".")
    if target not in available:
        print(f" Error: Cannot convert {input_path.suffix} to .{target}")
        print(f"   Available formats: {', '.join(available)}")
        return 1

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    converter = get_converter(category)
    if not converter:
        print(f" Error: No converter available for category '{category}'")
        return 1

    options = {}
    if args.quality is not None:
        options["quality"] = args.quality

    try:
        print(f"🍋 Converting {input_path.name} → .{target}...")
        output_path = converter.convert(str(input_path), target, output_dir=str(output_dir) if output_dir else None, **options)
        print(f"Done! Output: {output_path}")
        return 0
    except Exception as e:
        print(f" Conversion failed: {e}")
        return 1


def cmd_info(args):
    """Show file information and metadata."""
    input_path = Path(args.file).resolve()
    if not input_path.exists():
        print(f" Error: File not found: {input_path}")
        return 1

    category = get_category(str(input_path))
    if not category:
        print(f" Error: Unsupported file type: {input_path.suffix}")
        return 1

    print(f"File: {input_path.name}")
    print(f"   Path: {input_path}")
    print(f"   Size: {_format_size(input_path.stat().st_size)}")
    print(f"   Category: {category}")
    print(f"   Format: {input_path.suffix.lstrip('.')}")

    # Try to get detailed info from the appropriate tool
    tool = get_tool(category)
    if tool and hasattr(tool, "get_info"):
        try:
            info = tool.get_info(str(input_path))
            if info:
                print(f"\n Details:")
                for key, value in info.items():
                    print(f"      {key}: {value}")
        except Exception:
            pass

    # Show available conversions
    conversions = get_conversions_for_file(str(input_path))
    if conversions:
        print(f"\n    Can convert to: {', '.join(conversions)}")

    # Show available tools
    tools = get_tools_for_file(str(input_path))
    if tools:
        print(f"Available tools: {', '.join(tools)}")

    return 0


def cmd_formats(args):
    """List supported formats."""
    if args.file_or_category:
        # Check if it's a file or category name
        query = args.file_or_category
        if os.path.exists(query):
            category = get_category(query)
            if not category:
                print(f" Unsupported file type")
                return 1
            conversions = get_conversions_for_file(query)
            print(f"Conversion targets for {Path(query).suffix}:")
            for fmt in conversions:
                print(f"   → .{fmt}")
        elif query.lower() in CATEGORY_MAP:
            category = query.lower()
            print(f"📁 Formats in '{category}' category:")
            for ext, info in FORMAT_REGISTRY.items():
                if info.category == category:
                    print(f"   .{ext:8s} — {info.display_name}")
        else:
            print(f" Unknown category or file: {query}")
            print(f"   Categories: {', '.join(CATEGORY_MAP.keys())}")
            return 1
    else:
        print("Supported Format Categories:\n")
        for category, cat_info in CATEGORY_MAP.items():
            formats = [ext for ext, f in FORMAT_REGISTRY.items() if f.category == category]
            print(f"  {category.upper():10s} ({len(formats)} formats)")
            print(f"    {', '.join('.' + f for f in formats)}\n")
    return 0


def cmd_tools(args):
    """Run a tool on a file."""
    input_path = Path(args.file).resolve()
    if not input_path.exists():
        print(f" Error: File not found: {input_path}")
        return 1

    category = get_category(str(input_path))
    if not category:
        print(f" Error: Unsupported file type: {input_path.suffix}")
        return 1

    available_tools = get_tools_for_file(str(input_path))
    tool_name = args.tool_name.lower()

    if tool_name not in available_tools:
        print(f" Error: Tool '{tool_name}' not available for this file type")
        print(f"   Available tools: {', '.join(available_tools)}")
        return 1

    tool = get_tool(category)
    if not tool:
        print(f" Error: No tools available for category '{category}'")
        return 1

    method = getattr(tool, tool_name, None)
    if not method:
        print(f" Error: Tool method '{tool_name}' not found")
        return 1

    # Build kwargs from remaining args
    kwargs = _parse_tool_options(args.options)

    try:
        print(f" Running {tool_name} on {input_path.name}...")
        result = method(str(input_path), **kwargs)
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"   {key}: {value}")
        elif isinstance(result, str):
            print(f"Done! Output: {result}")
        else:
            print(f"Done!")
        return 0
    except Exception as e:
        print(f" Tool failed: {e}")
        return 1


def cmd_batch(args):
    """Batch convert files in a directory."""
    input_dir = Path(args.input_dir).resolve()
    if not input_dir.is_dir():
        print(f" Error: Not a directory: {input_dir}")
        return 1

    target = args.output_format.lower().lstrip(".")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None

    # Collect files
    if args.recursive:
        files = list(input_dir.rglob("*"))
    else:
        files = list(input_dir.iterdir())

    # Filter to convertible files
    convertible = []
    for f in files:
        if f.is_file():
            category = get_category(str(f))
            if category:
                conversions = get_conversions_for_file(str(f))
                if target in conversions:
                    convertible.append((f, category))

    if not convertible:
        print(f" No files found that can be converted to .{target}")
        return 1

    print(f"🍋 Batch converting {len(convertible)} files → .{target}...")
    success = 0
    failed = 0

    for filepath, category in convertible:
        converter = get_converter(category)
        if not converter:
            continue
        try:
            out = converter.convert(
                str(filepath), target,
                output_dir=str(output_dir) if output_dir else None,
            )
            print(f"  {filepath.name} → {Path(out).name}")
            success += 1
        except Exception as e:
            print(f"   {filepath.name}: {e}")
            failed += 1

    print(f"\n Results: {success} converted, {failed} failed")
    return 0


def cmd_check_deps(args):
    """Check which system dependencies are installed."""
    import shutil

    deps = {
        "ffmpeg": "Video/Audio conversion",
        "ffprobe": "Media file analysis",
        "convert": "Image conversion (ImageMagick)",
        "identify": "Image info (ImageMagick)",
        "pandoc": "Document conversion",
        "libreoffice": "Office document conversion",
        "7z": "7-Zip archive support",
        "exiftool": "Metadata reading/writing",
        "qpdf": "PDF manipulation",
        "gs": "Ghostscript (PDF fallback)",
    }

    print("Checking system dependencies...\n")
    all_ok = True
    for cmd, desc in deps.items():
        path = shutil.which(cmd)
        if path:
            print(f"  {cmd:15s} — {desc}")
        else:
            print(f"   {cmd:15s} — {desc} (NOT FOUND)")
            all_ok = False

    if all_ok:
        print("\n All dependencies are installed!")
    else:
        print("\n Install missing dependencies with:")
        print("   sudo apt install ffmpeg imagemagick pandoc libreoffice-core p7zip-full libimage-exiftool-perl qpdf ghostscript")

    return 0


def _format_size(size_bytes):
    """Format file size in human-readable form."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _parse_tool_options(options_list):
    """Parse tool options from --key value pairs."""
    kwargs = {}
    i = 0
    while i < len(options_list):
        opt = options_list[i]
        if opt.startswith("--"):
            key = opt[2:].replace("-", "_")
            if i + 1 < len(options_list) and not options_list[i + 1].startswith("--"):
                value = options_list[i + 1]
                # Try to convert to number
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                kwargs[key] = value
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            i += 1
    return kwargs


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="elumichai-cli",
        description=f"🍋 {__app_name__} v{__version__} — Free, offline file conversion tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run 'elumichai-cli <command> --help' for more info on a command.",
    )
    parser.add_argument("--version", action="version", version=f"{__app_name__} v{__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # convert
    p_convert = subparsers.add_parser("convert", help="Convert a file to another format")
    p_convert.add_argument("input_file", help="Input file path")
    p_convert.add_argument("output_format", help="Target format (e.g., png, mp4, pdf)")
    p_convert.add_argument("--output-dir", "-o", help="Output directory (default: same as input)")
    p_convert.add_argument("--quality", "-q", type=int, help="Quality (1-100, for image/video)")
    p_convert.set_defaults(func=cmd_convert)

    # info
    p_info = subparsers.add_parser("info", help="Show file information")
    p_info.add_argument("file", help="File to inspect")
    p_info.set_defaults(func=cmd_info)

    # formats
    p_formats = subparsers.add_parser("formats", help="List supported formats")
    p_formats.add_argument("file_or_category", nargs="?", help="File path or category name")
    p_formats.set_defaults(func=cmd_formats)

    # tools
    p_tools = subparsers.add_parser("tools", help="Run a tool on a file")
    p_tools.add_argument("tool_name", help="Tool name (e.g., compress, resize, trim)")
    p_tools.add_argument("file", help="Input file")
    p_tools.add_argument("options", nargs=argparse.REMAINDER, help="Tool options (--key value)")
    p_tools.set_defaults(func=cmd_tools)

    # batch
    p_batch = subparsers.add_parser("batch", help="Batch convert files in a directory")
    p_batch.add_argument("input_dir", help="Input directory")
    p_batch.add_argument("output_format", help="Target format")
    p_batch.add_argument("--output-dir", "-o", help="Output directory")
    p_batch.add_argument("--recursive", "-r", action="store_true", help="Process subdirectories")
    p_batch.set_defaults(func=cmd_batch)

    # check-deps
    p_deps = subparsers.add_parser("check-deps", help="Check installed system dependencies")
    p_deps.set_defaults(func=cmd_check_deps)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
