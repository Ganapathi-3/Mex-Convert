#!/usr/bin/env python3
"""
Citrus Converter - Main Entry Point

Launches either the GUI application or the CLI based on arguments.

Usage:
    citrus-converter              # Launch GUI
    citrus-converter --cli ...    # Use CLI mode
    citrus-converter --help       # Show help
"""

import sys
import os


def main():
    """Main entry point - decides between GUI and CLI mode."""
    # Check if running in CLI mode
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # Remove the --cli flag and pass rest to CLI
        sys.argv.pop(1)
        from citrus_converter.cli import main as cli_main
        return cli_main()

    # Check if running in CLI mode via direct command names
    cli_commands = {"convert", "info", "formats", "tools", "batch", "check-deps"}
    if len(sys.argv) > 1 and sys.argv[1] in cli_commands:
        from citrus_converter.cli import main as cli_main
        return cli_main()

    # Launch GUI
    try:
        from citrus_converter.app import CitrusApp
        app = CitrusApp(sys.argv)
        if getattr(app, "_already_running", False):
            return 0
        return app.exec()
    except ImportError as e:
        print(f"GUI dependencies not available: {e}")
        print("   Install PySide6: python3 -m pip install PySide6")
        print("   Or use CLI mode: citrus-converter --cli convert file.png jpg")
        return 1
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        print("   Try CLI mode: citrus-converter --cli convert file.png jpg")
        return 1


if __name__ == "__main__":
    sys.exit(main())
