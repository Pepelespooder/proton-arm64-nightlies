# Developer Guide: Proton ARM64 Bleeding-Edge Build System

## Overview

The workflow builds Android-targeted Wine from Valve `bleeding-edge`, then layers in GameNative's Android and ARM64EC build system and local drift-fix scripts.

Current high-level flow:

1. Clone `ValveSoftware/wine` at `bleeding-edge`
2. Clone `GameNative/proton-wine` at `proton_10.0`
3. Copy GameNative `android/` and `build-scripts/` into the Valve tree
4. Apply local fix scripts for patch drift and ARM64EC-specific build issues
5. Build and install with Android NDK r27d and llvm-mingw
6. Package:
   - `proton-*.wcp` with Zstandard
   - `proton-wine-*.wcp.xz` with XZ

That local patch layer includes `patches/ge-gamenative-firstpass/explorer/explorer_startmenu_shutdown_latch.patch`, which avoids the blank mouse-only screen after exiting from the Start menu or a shortcut-launched game.
It can also opt into the local `ntsync` patch chain from `patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0163-...0166-...` for explicit test builds.

## Important Current Decisions

### Source refs

- `wine_ref=bleeding-edge`
- `gamenative_ref=proton_10.0`

### External vs internal naming

External release naming stays on `bleeding-edge`, but the GameNative-facing internal profile version is currently:

```text
10.0.99-arm64ec
```

That is deliberate. Stock GameNative only recognizes ARM64EC Proton when the internal version remains parser-compatible and numeric.

### Install path alignment

The build is baked against:

```text
/data/data/com.winlator.cmod/files/imagefs/opt/proton-10.0.99-arm64ec
```

That path is chosen to match how the packaged runtime is imported and used at runtime. This fixed the earlier `kernel32.dll` startup failure caused by building against `/opt/wine`.

### No donor overlay

The workflow no longer contains any donor or kernel compatibility overlay step. The build path is now single-mode and deterministic.

## Packaging Outputs

### GameNative package

- Filename pattern: `proton-proton-bleeding-edge-YYYYMMDD-HASH-arm64ec.wcp`
- Compression: Zstandard
- Profile type: `Proton`

### Compatibility package

- Filename pattern: `proton-wine-proton-bleeding-edge-YYYYMMDD-HASH-arm64ec.wcp.xz`
- Compression: XZ
- Intended for Ludashi/CMOD-style consumers

## Toolchains

- Android NDK r27d
- Android target API 28
- llvm-mingw for PE and ARM64EC components

`clang` is the correct compiler family here. This is an Android/bionic build, not desktop Proton.

## Environment Variables

The runtime environment variable reference lives in [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

The current repo-specific entries are centered on Android input toggles, optional debug toggles, and bundled Wine or Proton runtime variables rather than build-script configuration.

## Local Build Notes

If you build locally, mirror the workflow assumptions:

- use Valve `bleeding-edge`
- use GameNative `proton_10.0`
- keep the internal profile version and baked install path aligned

If you change the internal profile version, update both:

- `PROFILE_VERSION`
- baked `INSTALL_DIR`

Those must continue to point at the same `/opt/proton-*` directory.

## Testing Priorities

1. Confirm the package imports
2. Confirm the runtime launches from `/opt/proton-10.0.99-arm64ec`
3. Confirm there is no fallback to `/opt/wine`
4. Confirm there is no `could not load kernel32.dll`
5. Only then debug game-specific runtime failures
