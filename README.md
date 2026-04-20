# Exe2Iconset

Cross-platform tool to extract icons from Windows EXE/DLL files and create macOS ICNS files.

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

1. **Select EXE File**: Click "Browse..." to select a Windows executable (EXE, DLL, MUN)
2. **Extract Icons**: Click "Extract Icons" to extract icon groups from the PE file
3. **Select Series**: Choose an icon series from the list in Step 2
4. **Create ICNS**: Enter output name and click "Create ICNS"
5. **Save Location**: ICNS file will be saved in the selected output directory

### CLI

```bash
# Using the installed command
exe2iconset <file.exe> --list

# Or with python -m
python -m exe2iconset <file.exe> --list

# Create ICNS from specific group
exe2iconset <file.exe> -g icongroup_47_1033 -o output.icns

# Create ICNS with iconset directory for inspection
exe2iconset <file.exe> -o output.icns --iconset
```

#### CLI Examples

```bash
# List all icon groups in a file
exe2iconset app.exe --list

# Extract icons using the first available group
exe2iconset app.exe -o app.icns

# Extract from a specific group (shown in --list output)
exe2iconset app.exe -g icongroup_3_1033 -o myapp.icns

# Create iconset directory for manual inspection
exe2iconset app.exe -o app.icns --iconset

# Verbose output
exe2iconset app.exe -o app.icns -v
```

#### CLI Options

| Option | Description |
|--------|-------------|
| `-l, --list` | List available icon groups and exit |
| `-g, --group GROUP` | Icon group to use (e.g., icongroup_3_1033) |
| `-o, --output FILE` | Output ICNS file (default: appicon.icns) |
| `--iconset` | Also create iconset directory |
| `-v, --verbose` | Enable verbose output |

## Python API

```python
from exe2iconset import extract_icons_from_pe, create_icns_from_images, convert_icons_to_icns_sizes, ICON_TYPE_MAP

# Extract icons from PE file
icon_groups = extract_icons_from_pe("app.exe")

# Convert extracted icons to PIL images with resolutions, sutable for ICNS
mac_icon_sizes = list(ICON_TYPE_MAP.keys())
convert_icons_to_icns_sizes(icon_data_list, mac_icon_sizes)

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
