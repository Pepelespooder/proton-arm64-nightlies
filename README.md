# Proton ARM64 Bleeding-Edge Builds for Winlator

Automated Proton ARM64 builds for Android, based on Valve's `bleeding-edge` Wine branch with GameNative's Android and ARM64EC patch stack layered on top.

This repo currently produces two artifacts per build:

| File | Use |
|------|-----|
| `proton-*.wcp` | GameNative / Proton import |
| `proton-wine-*.wcp.xz` | Ludashi / CMOD-style import |

## Current Build Behavior

- Source Wine ref: `bleeding-edge`
- GameNative patch ref: `proton_10.0`
- External naming: `proton-bleeding-edge-YYYYMMDD-HASH-arm64ec`
- Internal GameNative profile version: `10.0.99-arm64ec`
- No donor or kernel compatibility overlay

The internal profile version stays numeric on purpose so stock GameNative recognizes the build as ARM64EC Proton without requiring an app-side parser change.

The build also carries the local explorer shutdown workaround so exiting from the Start menu or a shortcut-launched game returns cleanly instead of leaving the blank pointer screen reported in Winlator issue 55.

Optional `ntsync` support is available for manual builds and workflow-dispatch runs, but it is intentionally opt-in because it is a substantial sync backend change and depends on target kernel support.

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

- Base Wine source: [ValveSoftware/wine](https://github.com/ValveSoftware/wine) at `bleeding-edge`
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
