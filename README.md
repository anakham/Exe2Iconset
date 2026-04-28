# Exe2Iconset

Cross-platform tool to extract icons from Windows EXE/DLL files, image files, or directories and create macOS ICNS files.

## Installation

### From PyPI (recommended)

```bash
pip install exe2iconset
```

### From source

```bash
pip install .
```

Or install in development mode:

```bash
pip install -e .
```

### Requirements

- Python >= 3.10
- Pillow >= 10.0.0
- pefile >= 2023.2.7

## Usage

### GUI

Run the GUI application:
```bash
# After pip install
exe2iconset-gui

# Or with python -m
python -m exe2iconset
```

Or import and run:
```python
from exe2iconset import run_gui
run_gui()
```

#### GUI Workflow

1. **Select Input File**: Click "Browse..." or enter path and press Enter
2. **Extract Icons**: Extraction starts automatically after file selection. A progress bar shows extraction progress.
3. **Select Series**: Choose an icon series from the Treeview list
4. **Create ICNS**: Enter output name and click "Create ICNS"
5. **Save Location**: ICNS file will be saved in the selected output directory

The icon list shows compact details like `ID:101, LANG:1033, all:64²×32bit` where:
- **ID**: Resource ID (e.g., 101)
- **LANG**: Language code (e.g., 1033 = English)
- **all**: All sizes in the group (e.g., 64²×32bit means 64x64 at 32-bit color)

Click the status bar to view the full activity log in a popup window.

### CLI

```bash
# Using the installed command
exe2iconset <file.exe> --list

# Or with python -m
python -m exe2iconset <file.exe> --list

# Create ICNS from specific group (PE files)
exe2iconset <file.exe> -g icongroup_47_1033 -o output.icns

# Create ICNS from image file
exe2iconset <image.png> -o output.icns

# Create ICNS with iconset directory for inspection
exe2iconset <file.exe> -o output.icns --iconset

# Verbose output for debugging
exe2iconset <file.exe> -v
```

### CLI Options

| Option | Description |
|--------|-------------|
| `-l, --list` | List available icon groups and exit |
| `-g, --group GROUP` | Icon group to use (e.g., icongroup_3_1033) |
| `-o, --output FILE` | Output ICNS file (default: appicon.icns) |
| `--iconset` | Also create iconset directory |
| `-v, --verbose` | Enable verbose output |

## Python API

```python
from exe2iconset import extract_images, create_icns_from_images, convert_icons_to_icns_sizes, ICON_TYPE_MAP

# Extract icons/images from PE file, image file, or directory
# Returns dict mapping group name to list of icon dicts
icon_groups = extract_images("app.exe")        # PE file
icon_groups = extract_images("image.png")      # Single image
icon_groups = extract_images("images/")        # Directory

# Get the first group (or specific group by name)
first_group_key = list(icon_groups.keys())[0]
icon_data_list = icon_groups[first_group_key]

# Convert extracted icons to PIL images with resolutions, suitable for ICNS
mac_icon_sizes = list(ICON_TYPE_MAP.keys())
icon_images = convert_icons_to_icns_sizes(icon_data_list, mac_icon_sizes)

# Create ICNS from images
create_icns_from_images(icon_images, "app.icns")

# Also you can save images as iconset directory
save_iconset(icon_images, "app.iconset")
```

## ICNS Format

The application creates ICNS files with these standard macOS icon types:

| Type | Size | Format | Notes |
|------|------|--------|-------|
| ic04 | 16×16 | ARGB | PackBits compressed |
| ic05 | 32×32 | ARGB | PackBits compressed |
| icp6 | 48×48 | PNG | |
| ic12 | 64×64 | PNG | Can serve as 32@2x retina |
| ic07 | 128×128 | PNG | |
| ic08 | 256×256 | PNG | |
| ic09 | 512×512 | PNG | |
| ic10 | 1024×1024 | PNG | Can serve as 512@2x retina |

### Notes on ICNS

- ARGB format (ic04/ic05) preserves alpha channel correctly
- PNG format is used for larger icons
- Retina versions are handled automatically by macOS - no need to create explicit @2x variants
- The ICNS format is flexible - only the sizes available from the source are included

For details on ICNS format, see:
- https://en.wikipedia.org/wiki/Apple_Icon_Image_format
- https://github.com/anakham/Exe2Iconset/issues

## Testing

Run tests with pytest:

```bash
# Install test dependencies
pip install exe2iconset[dev]

# Or install from source with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Known Issues

### Drag and Drop on macOS with Tcl/Tk 9.x

If the GUI fails to start with an error like "RuntimeError: Unable to load tkdnd library" or "this extension is compiled for Tcl 8.x", this indicates a Tcl/Tk version incompatibility.

**Problem**: tkinterdnd2's tkdnd extension is compiled for Tcl 8.x, but macOS with Homebrew may have Tcl/Tk 9.x linked by default.

**Solution**: Download and replace tkdnd binaries with Tcl 9.x compatible ones:

1. Download from https://github.com/petasis/tkdnd/releases:
   - For Apple Silicon (M1/M2/M3): `tkdnd-2.9.5-macOS-tcl9.0-arm64-x64-14.2.1.tgz`
   - For Intel Macs: `tkdnd-2.9.5-macOS-tcl9.0-x86_64-x64-14.2.1.tgz`

2. Extract the archive and copy contents to your tkinterdnd2 installation:
   ```bash
   # Find your tkinterdnd2 location
   python -c "import tkinterdnd2; print(tkinterdnd2.__file__)"
   
   # Navigate to tkdnd folder and replace files from the archive
   # The archive contains osx-arm64/ or osx-x64/ folder with:
   # - libtkdnd2.X.X.dylib (the binary)
   # - pkgIndex.tcl
   # - *.tcl files
   ```

Alternatively, try linking Tcl/Tk 8.x via Homebrew (may require rebuilding your virtual environment):
```bash
brew install tcl-tk@8
brew unlink tcl-tk
brew link tcl-tk@8
```

### Drag and Drop on Linux/Wayland

On some Linux distributions running Wayland, drag-and-drop from file managers may work inconsistently (sometimes fires, sometimes doesn't). This is a known tkinterdnd2 limitation with Wayland's inter-app DnD protocol.

**Workaround**: Use the "Browse..." button to select files, or try running with X11 session instead of Wayland.
