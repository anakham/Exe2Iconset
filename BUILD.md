# Building Application Bundle

## Local Build

To build the macOS `.app` bundle locally:

```bash
# Install build dependencies
pip install -e ".[dev]"

# Build the application
pyinstaller exe2iconset.spec --noconfirm

# Or use the helper script
python scripts/build_app.py
```

The built application will be in `dist/Exe2Iconset/`.

## GitHub Releases

The `.app` bundle is automatically built when you publish a GitHub release:

1. Go to the Releases page
2. Click "Draft a new release"
3. Enter version tag (e.g., `v0.x.x`)
4. Add release notes
5. Click "Publish release"

The workflow will build both x86_64 and arm64 (Apple Silicon) versions and create `.dmg` installers.