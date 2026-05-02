#!/usr/bin/env python3
"""Entry point for python -m exe2iconset and for PyInstaller bundle."""

import sys
from exe2iconset.gui import run_gui
from exe2iconset.cli import main as cli_main


def main():
    """Hybrid entry point: runs GUI by default, CLI if arguments provided."""
    if len(sys.argv) > 1:
        sys.exit(cli_main())
    else:
        run_gui()


if __name__ == "__main__":
    main()