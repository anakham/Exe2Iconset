import sys
import argparse
from exe2iconset.gui import run_gui
from exe2iconset.cli import main as cli_main


def main():
    """Entry point for python -m exe2iconset."""
    # Check for --gui flag first
    if '--gui' in sys.argv:
        sys.argv.remove('--gui')
        run_gui()
    elif len(sys.argv) > 1 and sys.argv[1] == '--gui':
        sys.argv[1] = ''
        run_gui()
    else:
        # Run CLI
        sys.exit(cli_main())


if __name__ == "__main__":
    main()
