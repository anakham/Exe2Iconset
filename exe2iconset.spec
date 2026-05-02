# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Exe2Iconset application.

Supports macOS, Linux, and Windows builds with platform-specific settings.
"""

import platform
import sys
from pathlib import Path

block_cipher = None
_root = Path(SPECPATH)

# Detect target platform from environment or auto-detect
# Can be overridden via PYINSTALLER_PLATFORM environment variable
_target = platform.system().lower()
if _target == 'darwin':
    _target = 'macos'
elif _target == 'windows':
    _target = 'windows'

# Hidden imports for all platforms
_hiddenimports = [
    'PIL._tkinter_finder',
    'tkinterdnd2',
    'tkinterdnd2.TkinterDnD',
]

# Binary name - set once to avoid case-insensitive FS conflicts on macOS
_binary_name = 'exe2iconset-run'

# Platform-specific icon
if _target == 'macos':
    _icon_path = _root / 'assets/icon/na-tro-ih.icns'
elif _target == 'windows':
    _icon_path = _root / 'assets/icon/na-tro-ih.ico'
else:
    _icon_path = None

# Platform-specific Analysis configuration
a = Analysis(
    [str(_root / 'exe2iconset' / '__main__.py')],
    pathex=[str(_root / 'exe2iconset')],
    binaries=[],
    datas=[],
    hiddenimports=_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=_binary_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=(_target != 'macos'),
    icon=str(_icon_path) if _icon_path else None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Exe2Iconset', # This is the folder name inside dist/
)

if _target == 'macos':
    app = BUNDLE(
        coll,
        name='Exe2Iconset.app',
        icon=str(_icon_path) if _icon_path else None,
        bundle_identifier='com.anakham.exe2iconset',
        info_plist={
            'CFBundleName': 'Exe2Iconset',
            'CFBundleDisplayName': 'Exe2Iconset',
            'CFBundleVersion': '0.2.0',
            'CFBundleShortVersionString': '0.2.0',
            'CFBundlePackageType': 'APPL',
            'CFBundleExecutable': _binary_name,
            'LSMinimumSystemVersion': '10.13',
            'NSHighResolutionCapable': True,
        },
    )
# Linux and Windows don't use BUNDLE - just use COLLECT output