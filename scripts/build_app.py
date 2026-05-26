#!/usr/bin/env python3
"""Build helper script for creating Exe2Iconset application bundles.

This script creates a virtual environment, installs dependencies,
and builds the application using PyInstaller.

Supports multiple platforms: macOS, Linux, Windows.
Supports packaging: ZIP, DMG (macOS), AppImage (Linux).
"""

import argparse
import os
import shutil
import subprocess
import sys
import platform
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent
VENV_DIR = PROJECT_DIR / ".venv"
SPEC_FILE = "exe2iconset.spec"


def get_current_platform():
    """Detect current platform."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    return "unknown"


def get_venv_python():
    """Get the path to Python in the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_venv_pip():
    """Get the path to pip in the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def get_venv_pyinstaller():
    """Get the path to pyinstaller in the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pyinstaller.exe"
    return VENV_DIR / "bin" / "pyinstaller"


def create_venv():
    """Create virtual environment if it doesn't exist."""
    if VENV_DIR.exists():
        print(f"Virtual environment already exists at {VENV_DIR}")
        return

    print(f"Creating virtual environment at {VENV_DIR}...")
    result = subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)])
    if result.returncode != 0:
        print("ERROR: Failed to create virtual environment", file=sys.stderr)
        sys.exit(1)
    print("Virtual environment created.")


def install_dependencies():
    """Install project dependencies in the venv."""
    print("Installing dependencies...")
    pip = get_venv_pip()
    result = subprocess.run([str(pip), "install", "-e", ".[dev]"])
    if result.returncode != 0:
        print("ERROR: Failed to install dependencies", file=sys.stderr)
        sys.exit(1)
    result = subprocess.run([str(pip), "install", "setuptools<72"])
    if result.returncode != 0:
        print("ERROR: Failed to install setuptools", file=sys.stderr)
        sys.exit(1)
    print("Dependencies installed.")


def clean_build():
    """Remove previous build artifacts."""
    dist_dir = PROJECT_DIR / "dist"
    build_dir = PROJECT_DIR / "build"

    if dist_dir.exists():
        print("Cleaning dist/...")
        shutil.rmtree(dist_dir)

    if build_dir.exists():
        print("Cleaning build/...")
        shutil.rmtree(build_dir)


def build(spec_file: str, clean: bool, target_platform: str):
    """Build application using PyInstaller."""
    if clean:
        clean_build()

    # Set environment for target platform
    env = os.environ.copy()
    if target_platform == "macos":
        env["PYINSTALLER_PLATFORM"] = "macos"
    elif target_platform == "linux":
        env["PYINSTALLER_PLATFORM"] = "linux"
    elif target_platform == "windows":
        env["PYINSTALLER_PLATFORM"] = "windows"

    pyinstaller = get_venv_pyinstaller()
    print(f"Building with PyInstaller using {spec_file} for {target_platform}...")

    result = subprocess.run([str(pyinstaller), spec_file, "--noconfirm"], env=env)
    if result.returncode != 0:
        print("ERROR: PyInstaller build failed", file=sys.stderr)
        sys.exit(1)

    output_dir = PROJECT_DIR / "dist"
    if target_platform == "macos":
        app_path = output_dir / "Exe2Iconset.app"
        # Ad-hoc sign the app bundle for better macOS compatibility
        print(f"Signing app bundle with ad-hoc signature...")
        sign_result = subprocess.run(
            ["codesign", "--force", "--deep", "--sign", "-", str(app_path)],
            capture_output=True,
        )
        if sign_result.returncode != 0:
            print(
                f"WARNING: codesign failed: {sign_result.stderr.decode()}",
                file=sys.stderr,
            )
        else:
            print(f"App bundle signed successfully.")
    else:
        app_path = output_dir / "Exe2Iconset"

    print(f"=== Build Complete ===")
    print(f"Output: {app_path}")
    return app_path


def _hide_dmg_folder(dmg_path: Path, volname: str, folder: str):
    """Set the UF_HIDDEN flag on a folder inside a compressed DMG.

    This makes the folder invisible in Finder even when "show hidden files" is enabled
    (Cmd+Shift+.), unlike the dot-prefix convention which only hides by default.
    """
    temp_dmg = dmg_path.with_suffix(".rw.dmg")
    mount_point = Path("/Volumes") / volname

    if temp_dmg.exists():
        temp_dmg.unlink()

    try:
        subprocess.run(
            [
                "hdiutil",
                "convert",
                str(dmg_path),
                "-format",
                "UDRW",
                "-o",
                str(temp_dmg),
                "-ov",
            ],
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["hdiutil", "attach", str(temp_dmg), "-mountroot", "/Volumes", "-nobrowse"],
            check=True,
            capture_output=True,
        )

        target = mount_point / folder
        if target.exists():
            subprocess.run(["chflags", "hidden", str(target)], check=True)
            print(f"Set hidden flag on {folder} inside DMG")

        subprocess.run(
            ["hdiutil", "detach", str(mount_point)],
            check=True,
            capture_output=True,
        )

        dmg_path.unlink()
        subprocess.run(
            [
                "hdiutil",
                "convert",
                str(temp_dmg),
                "-format",
                "UDZO",
                "-o",
                str(dmg_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        dmg_path.chmod(0o644)
    finally:
        if temp_dmg.exists():
            temp_dmg.unlink()


def create_dmg(app_path: Path, output_dir: Path):
    """Create DMG from app bundle using system create-dmg."""
    # Check if create-dmg is available
    check_result = subprocess.run(["which", "create-dmg"], capture_output=True)
    if check_result.returncode != 0:
        print("WARNING: create-dmg not found, falling back to ZIP")
        return create_zip(app_path, output_dir, "macos")

    dmg_name = f"Exe2Iconset-{platform.machine()}.dmg"
    dmg_path = output_dir / dmg_name

    # Remove existing DMG if present
    if dmg_path.exists():
        dmg_path.unlink()

    # Get background image and additional files
    background_img = PROJECT_DIR / "build" / "dmg_content" / "dmg_background.png"
    quarantine_txt = PROJECT_DIR / "assets" / "dmg_content" / "Exit Quarantine.txt"
    terminal_app = PROJECT_DIR / "assets" / "dmg_content" / "Terminal.app"

    print(f"Creating DMG: {dmg_path}...")

    # Build create-dmg command
    cmd = [
        "create-dmg",
        "--volname",
        "Exe2Iconset",
        "--window-pos",
        "200",
        "120",
        "--window-size",
        "480",
        "500",
        "--icon-size",
        "72",
        "--icon",
        "Exe2Iconset.app",
        "64",
        "110",
        "--text-size",
        "10",
        "--app-drop-link",
        "380",
        "110",
    ]

    # Add Exit Quarantine.txt file
    if quarantine_txt.exists():
        cmd.extend(
            ["--add-file", "Exit Quarantine.txt", str(quarantine_txt), "380", "210"]
        )

    # Add Terminal.app shortcut (check symlink, not target, since /System/Applications only exists on 10.15+)
    if terminal_app.is_symlink():
        cmd.extend(["--add-file", "Terminal.app", str(terminal_app), "380", "310"])

    # Add background if available
    if background_img.exists():
        cmd.extend(["--background", str(background_img)])

    # Add output path and source app
    cmd.extend([str(dmg_path), str(app_path)])

    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("WARNING: Failed to create DMG, falling back to ZIP")
        return create_zip(app_path, output_dir)

    print(f"DMG created: {dmg_path}")

    # Hide .background folder so it's invisible even with Finder's "show hidden files" enabled
    if background_img.exists():
        _hide_dmg_folder(dmg_path, "Exe2Iconset", ".background")


def create_zip(app_path: Path, output_dir: Path, platform: str = None):
    """Create ZIP from app bundle or directory."""
    import zipfile

    if platform:
        zip_name = f"Exe2Iconset-{platform}.zip"
    elif app_path.suffix == ".app":
        zip_name = f"{app_path.stem}.zip"
    else:
        zip_name = f"{app_path.name}-portable.zip"

    zip_path = output_dir / zip_name

    print(f"Creating ZIP: {zip_path}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if app_path.is_dir():
            for item in app_path.rglob("*"):
                if item.is_file():
                    arcname = str(item.relative_to(app_path.parent))
                    zf.write(item, arcname)

    print(f"ZIP created: {zip_path}")
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Build Exe2Iconset application bundle")
    parser.add_argument(
        "--clean", action="store_true", help="Clean build directory before building"
    )
    parser.add_argument(
        "--spec", default=SPEC_FILE, help="Spec file path (default: %(default)s)"
    )
    parser.add_argument(
        "--platform",
        choices=["auto", "macos", "linux", "windows"],
        default="auto",
        help="Target platform (default: auto-detect)",
    )
    parser.add_argument(
        "--no-dmg",
        action="store_true",
        help="Skip DMG creation on macOS, use ZIP instead",
    )
    parser.add_argument(
        "--package",
        choices=["none", "zip", "dmg", "appimage"],
        default="none",
        help="Package type (default: auto - DMG for macOS, ZIP for others)",
    )

    args = parser.parse_args()

    # Detect platform
    target_platform = (
        args.platform if args.platform != "auto" else get_current_platform()
    )
    print(f"Target platform: {target_platform}")

    # Determine packaging - auto-detect defaults
    package_type = args.package
    if package_type == "none":
        if target_platform == "macos" and not args.no_dmg:
            package_type = "dmg"
        else:
            package_type = "zip"

    # Validate package option for platform
    if package_type == "dmg" and target_platform != "macos":
        print("ERROR: DMG packaging is only supported on macOS", file=sys.stderr)
        sys.exit(1)

    if package_type == "appimage" and target_platform != "linux":
        print("ERROR: AppImage packaging is only supported on Linux", file=sys.stderr)
        sys.exit(1)

    # Build
    spec_path = PROJECT_DIR / args.spec
    if not spec_path.exists():
        print(f"ERROR: Spec file not found: {spec_path}", file=sys.stderr)
        sys.exit(1)

    create_venv()
    install_dependencies()
    app_path = build(args.spec, args.clean, target_platform)

    # Package
    output_dir = PROJECT_DIR / "dist"

    # Generate DMG background for macOS
    if package_type == "dmg" and target_platform == "macos":
        print("Generating DMG background...")
        bg_script = (
            PROJECT_DIR / "assets" / "dmg_content" / "generate_dmg_background.py"
        )
        if bg_script.exists():
            result = subprocess.run([str(get_venv_python()), str(bg_script)])
            if result.returncode != 0:
                print("WARNING: Failed to generate background", file=sys.stderr)

    if package_type == "zip":
        create_zip(app_path, output_dir, target_platform)
    elif package_type == "dmg":
        create_dmg(app_path, output_dir)
    elif package_type == "appimage":
        print("AppImage creation not yet implemented")


if __name__ == "__main__":
    main()
