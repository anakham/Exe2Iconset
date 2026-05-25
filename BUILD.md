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

## macOS High Sierra Build

For building a High Sierra-compatible `.app` bundle and `.dmg`, use the VMware dev helper scripts. This requires:

- VMware Fusion running on a host machine with SSH access
- A macOS 10.13 High Sierra VM with the dev environment set up
- SSH access configured via `~/.ssh/config` (host: `mac_hs_vm`, host: `mac-vm-host`)

### Prerequisites

SSH hosts are configured in `~/.ssh/config`:

```
Host mac-vm-host
  HostName <host-ip-or-hostname>
  User anatoly

Host mac_hs_vm
  HostName <vm-ip>
  User anatoly
```

The VM must have the project at `~/Projects/Exe2Iconset` with Python 3.10+ and dependencies installed.

### Build the App (on already-running VM)

```bash
scripts/vmware_dev_helpers/build_and_test --skip-activate --no-test --no-copy-local
```

This syncs the latest code, injects `SETUPTOOLS_SCM_PRETEND_VERSION` from the current git tag, and builds the app via PyInstaller.

### Build and Copy Artifacts

```bash
scripts/vmware_dev_helpers/build_and_test --skip-activate --no-test
```

This builds on the VM and copies the `.app` bundle, `.zip`, and `.dmg` back to `dist/`.

### Full Build Cycle (with snapshot management)

```bash
scripts/vmware_dev_helpers/build_and_test
```

This reverts the VM to the `PyInstallerDevelopment` snapshot, syncs code, builds, copies artifacts, and optionally tests the app on a fresh install.

### Options

| Flag | Description |
|---|---|
| `--skip-activate` | Skip VM snapshot revert (VM already running) |
| `--no-test` | Skip testing on fresh install |
| `--no-copy-local` | Skip copying artifacts back to local machine |
| `--clean` | Clean build directory before building |
| `--package dmg` | Create `.dmg` package (requires `create-dmg` on VM) |

### Snapshot Management

- **`scripts/vmware_dev_helpers/activate_dev_env`** — revert VM to `PyInstallerDevelopment` snapshot and start
- **`scripts/vmware_dev_helpers/activate_clean_state`** — revert VM to `Fresh Install` snapshot and start
- **`scripts/vmware_dev_helpers/save_dev_state`** — save current VM state as new `PyInstallerDevelopment` snapshot

## GitHub Releases

The `.app` bundle is automatically built when you publish a GitHub release:

1. Go to the Releases page
2. Click "Draft a new release"
3. Enter version tag (e.g., `v0.x.x`)
4. Add release notes
5. Click "Publish release"

The workflow will build both x86_64 and arm64 (Apple Silicon) versions and create `.dmg` installers.