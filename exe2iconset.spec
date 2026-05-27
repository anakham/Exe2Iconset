# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Exe2Iconset application.

Supports macOS, Linux, and Windows builds with platform-specific settings.
"""

import importlib
import logging
import platform
import sys
from pathlib import Path

# Monkey-patch PyInstaller's macOS code signing helpers on older macOS where
# codesign_allocate cannot process PKG-extended binaries.
#
# Patches:
#   1. remove_signature_from_binary — use macholib to strip LC_CODE_SIGNATURE
#      instead of relying on broken codesign --remove on 10.13 (which returns
#      0 but does nothing).
#   2. fix_exe_for_code_signing — catch AssertionError/SystemError (raised when
#      the OS-level codesign_allocate cannot process PKG-extended binaries).
#   3. sign_binary — catch SystemError (same codesign_allocate issue).
try:
    _osx = importlib.import_module('PyInstaller.utils.osx')

    # Patch 1: remove_signature — use macholib to manually strip LC_CODE_SIGNATURE
    # instead of relying on broken codesign --remove on 10.13 (which returns
    # 0 but does nothing).  Based on the approach from:
    # https://github.com/HinTak/mono-modification/blob/macosx-10.13/remove-code-signature.py
    #
    # LC_CODE_SIGNATURE is always the last load command.  We delete it, update
    # the header's ncmds/sizeofcmds, adjust __LINKEDIT.filesize, and truncate
    # the file to remove the signature blob.
    try:
        from macholib.MachO import MachO
        from macholib.mach_o import LC_CODE_SIGNATURE, LC_SYMTAB

        _orig_remove = _osx.remove_signature_from_binary
        def _patched_remove(filename):
            try:
                executable = MachO(filename)
                file_size = __import__('os').path.getsize(filename)
                modified = False
                last_symtab_end = 0

                for header in executable.headers:
                    if header.commands[-1][0].cmd != LC_CODE_SIGNATURE:
                        continue
                    # Find SYMTAB end — needed for LINKEDIT fixup
                    for c in header.commands:
                        if c[0].cmd == LC_SYMTAB:
                            last_symtab_end = c[1].stroff + c[1].strsize
                            break
                    # Remove LC_CODE_SIGNATURE (always last command)
                    removed = header.commands.pop()
                    header.header.ncmds -= 1
                    header.header.sizeofcmds -= removed[0].cmdsize
                    modified = True

                if modified:
                    # Update __LINKEDIT filesize/vmsize for the last header
                    linkedit = None
                    for c in executable.headers[-1].commands:
                        if hasattr(c[1], 'segname') and c[1].segname.startswith(b'__LINKEDIT'):
                            linkedit = c[1]
                            break
                    if linkedit:
                        linkedit.filesize = last_symtab_end - linkedit.fileoff
                        linkedit.vmsize = linkedit.filesize
                    # Write updated headers and truncate signature blob
                    with open(filename, 'rb+') as fp:
                        executable.write(fp)
                        fp.truncate(last_symtab_end)
            except Exception:
                _orig_remove(filename)
        _osx.remove_signature_from_binary = _patched_remove
    except ImportError:
        pass

    # Patch 2: fix_exe_for_code_signing — absorb AssertionError/SystemError
    _orig_fix = _osx.fix_exe_for_code_signing
    def _patched_fix(path):
        try:
            _orig_fix(path)
        except (AssertionError, SystemError) as _e:
            logging.getLogger().warning(
                "fix_exe_for_code_signing skipped on %s (expected on 10.13): %s", path, _e
            )
    _osx.fix_exe_for_code_signing = _patched_fix

    # Patch 3: sign_binary — absorb SystemError
    _orig_sign = _osx.sign_binary
    def _patched_sign(path, identity=None, entitlements=None, **kwargs):
        try:
            _orig_sign(path, identity, entitlements, **kwargs)
        except SystemError as _e:
            logging.getLogger().warning(
                "sign_binary skipped on %s (expected on 10.13): %s", path, _e
            )
    _osx.sign_binary = _patched_sign
except (ImportError, AttributeError):
    pass

# Read version from installed package at build time
try:
    from importlib.metadata import version as _get_version
    _app_version = _get_version("exe2iconset")
except Exception:
    _app_version = "0.0.0"

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
    console=False,
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
            'CFBundleVersion': _app_version,
            'CFBundleShortVersionString': _app_version,
            'CFBundlePackageType': 'APPL',
            'CFBundleExecutable': _binary_name,
            'LSMinimumSystemVersion': '10.13',
            'NSHighResolutionCapable': True,
        },
    )
# Linux and Windows don't use BUNDLE - just use COLLECT output