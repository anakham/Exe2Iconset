# Exe2Iconset

Cross-platform tool to extract icons from Windows EXE/DLL files and create macOS ICNS files.

## Installation

```bash
pip install Pillow pefile
```

## Usage

### GUI

Run the GUI application:
```bash
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
# List available icon groups
python -m exe2iconset <file.exe> --list

# Create ICNS from specific group
python -m exe2iconset <file.exe> -g icongroup_47_1033 -o output.icns

# Create ICNS with iconset directory for inspection
python -m exe2iconset <file.exe> -o output.icns --iconset
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
from exe2iconset import extract_icons_from_pe, create_icns_from_images

# Extract icons from PE file
icon_groups = extract_icons_from_pe("app.exe")

# Create ICNS from images
create_icns_from_images(icon_images, "app.icns")
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

Run tests:
```bash
PYTHONPATH=. python tests/test_icns.py
PYTHONPATH=. python tests/test_extract.py
PYTHONPATH=. python tests/test_convert.py
```

Or with pytest:
```bash
pip install pytest
PYTHONPATH=. pytest tests/
```
