# Proton ARM64 Proton_11 Builds for Winlator

Automated Proton ARM64 builds for Android, based on Valve's `proton_11.0` Proton branch with the Proton `wine/` submodule as the base source tree, then layered with GameNative's Android and ARM64EC patch stack.

This repo currently produces two artifacts per build:

| File | Use |
|------|-----|
| `proton-*.wcp` | GameNative / Proton import |
| `proton-wine-*.wcp.xz` | Ludashi / CMOD-style import |

## Current Build Behavior

- Source Proton ref: `proton_11.0`
- GameNative patch ref: `proton_10.0`
- External naming: `proton-proton_11-YYYYMMDD-HASH-arm64ec`
- Internal GameNative profile version: `11`
- No donor or kernel compatibility overlay

The internal profile version stays numeric on purpose so stock GameNative recognizes the build as ARM64EC Proton without requiring an app-side parser change.

The build also carries the local explorer shutdown workaround so exiting from the Start menu or a shortcut-launched game returns cleanly instead of leaving the blank pointer screen reported in Winlator issue 55.

Optional `ntsync` support is available for manual builds and workflow-dispatch runs, but it is intentionally opt-in because it is a substantial sync backend change and depends on target kernel support. In these builds, ntsync only auto-enables when `/dev/ntsync` is actually openable by the app process; `WINENTSYNC=1` still force-enables it, and `WINENTSYNC=0` disables it.

There is also an optional GE compatibility bundle for manual builds and workflow-dispatch runs. The current first-pass set is intentionally small and focused on broad app compatibility: the D2D no-target crash fix, the `win32u` window-decoration env switch, and the registry `RRF_RT_REG_SZ`/`RRF_RT_REG_EXPAND_SZ` fix.

## Getting a Build

1. Open [Releases](../../releases)
2. Download the latest `proton-*.wcp` for GameNative
3. Copy it to your Android device
4. Import it from the app's Wine/Proton import UI

For Ludashi/CMOD-style imports, use the matching `proton-wine-*.wcp.xz` artifact instead.

## What's Inside

Each build includes:

- Android ARM64 Wine binaries built with Android NDK r27d
- ARM64EC Windows PE DLLs
- ARM64 and 32-bit WoW64 PE DLLs
- A default `prefixPack.txz`

## Source Layout

- Base source: [ValveSoftware/Proton](https://github.com/ValveSoftware/Proton/tree/proton_11.0) at `proton_11.0`, using its `wine/` submodule as `wine-source`
- Android and ARM64EC patches/build scripts: [GameNative/proton-wine](https://github.com/GameNative/proton-wine) at `proton_10.0`

## Build Status

The workflow runs daily at 2 AM UTC and can also be started manually from the [Actions tab](../../actions). [latest.json](latest.json) tracks the latest successful build.

## Docs

- [WCP_STRUCTURE.md](docs/WCP_STRUCTURE.md)
- [BUILD_REQUIREMENTS.md](docs/BUILD_REQUIREMENTS.md)
- [BUILD_ISSUES.md](docs/BUILD_ISSUES.md)
- [ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md)
- [USER_GUIDE.md](docs/USER_GUIDE.md)
- [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)

## License

This repository is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE).
