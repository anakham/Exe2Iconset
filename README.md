# Exe2Iconset
Conversion of icons from windows files (exe, dll, etc) to MacOS iconset package. Application. This README was taken from deepseek quary with prompt:

```
I need python program with tk ui backend which: 1) will extract resources from windows executable file by means of 7z archive console application; 2) will find among extracted files icon series of images and show it on application pane; 3) will take icon files from user selected series and, treating them as png, prepare macos icns series of file with correct resolution sequence for macos iconset; 4) create iconset macos package using console util
```

Code placed to [exe2iconset.py](./exe2iconset.py), and code wrapping text from deepseek answer is bellow. Some errors were fixed, look at issues and history.

# Windows Executable Icon Extractor and macOS ICNS Creator

Here's a comprehensive Python application with Tkinter UI that extracts icons from Windows executables, displays them, and converts them to macOS ICNS format


## Installation Requirements

Before running the application, install the required dependencies:

```bash
pip install Pillow
```

Also, you need to have **7-Zip** installed and available in your PATH. You can download it from [https://www.7-zip.org/](https://www.7-zip.org/).

## Key Features

1. **EXE File Selection**: Browse and select Windows executable files
2. **Icon Extraction**: Uses 7-Zip to extract resources from EXE files
3. **Icon Display**: Shows extracted icons grouped by series
4. **Series Selection**: Choose which icon series to convert
5. **ICNS Conversion**: Creates macOS iconset with proper resolutions
6. **Cross-platform**: Works on Windows, macOS, and Linux

## Usage Instructions

1. **Select EXE File**: Click "Browse..." to select a Windows executable
2. **Extract Icons**: Click "Extract Icons" to extract and display icons
3. **Select Series**: Choose an icon series from the displayed options
4. **Convert to ICNS**: Enter output name and click "Create ICNS Package"
5. **Save Location**: Choose where to save the macOS iconset

## Note for macOS ICNS Creation

- On **macOS**, the application will use the native `iconutil` command to create the final `.icns` file
- On **Windows/Linux**, it will create the iconset directory with all PNG files and provide instructions for final conversion on macOS

## Required macOS Icon Sizes

The application automatically creates icons in these standard macOS sizes:
- 16x16, 32x32, 64x64, 128x128, 256x256, 512x512, 1024x1024 pixels
- Both regular and @2x (retina) versions where possible

The application handles errors gracefully and provides status updates throughout the process.

For the latest issue list and details, see: https://github.com/anakham/Exe2Iconset/issues