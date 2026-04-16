# Developer Guide: Proton ARM64 Proton_11 Build System

## Overview

The workflow builds Android-targeted Wine from Valve Proton `proton_11.0` by checking out Proton and using its `wine/` submodule as the working source tree, then layers in GameNative's Android and ARM64EC build system and local drift-fix scripts.

Current high-level flow:

1. Clone `ValveSoftware/Proton` at `proton_11.0`
2. Initialize Proton's `wine/` submodule and use it as `wine-source`
3. Clone `GameNative/proton-wine` at `proton_10.0`
4. Copy GameNative `android/` and `build-scripts/` into the Wine tree
5. Apply local fix scripts for patch drift and ARM64EC-specific build issues
6. Build and install with Android NDK r27d and llvm-mingw
7. Package:
   - `proton-*.wcp` with Zstandard
   - `proton-wine-*.wcp.xz` with XZ

That local patch layer includes `patches/ge-gamenative-firstpass/explorer/explorer_startmenu_shutdown_latch.patch`, which avoids the blank mouse-only screen after exiting from the Start menu or a shortcut-launched game.
It can also opt into the local `ntsync` patch chain from `patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0163-...0166-...` for explicit test builds. The repo-side ntsync gate now auto-enables only when `/dev/ntsync` can actually be opened; `WINENTSYNC=1` force-enables it and `WINENTSYNC=0` disables it.
The optional GE performance bundle now also includes the generic `opengl32` wow64 buffer-mapping speedup series from that tree: `0113`, `0114`, `0115`, and `0127`, plus the existing `6559c43` AFD completion patch.
The optional GE compatibility bundle currently carries three low-risk first-pass patches from the repo classification set: `fix-a-crash-in-ID2D1DeviceContext-if-no-target-is-set.patch`, `0001-win32u-add-env-switch-to-disable-wm-decorations.patch`, and `registry_RRF_RT_REG_SZ-RRF_RT_REG_EXPAND_SZ.patch`.

## Important Current Decisions

### Source refs

- `wine_ref=proton_11.0`
- `gamenative_ref=proton_10.0`

### External vs internal naming

External release naming now follows `proton_11.0`, but the GameNative-facing internal profile version is currently:

```text
11
```

That is deliberate. Stock GameNative only recognizes ARM64EC Proton when the internal version remains parser-compatible and numeric.

### Install path alignment

The build is baked against:

```text
/data/data/com.winlator.cmod/files/imagefs/opt/proton-11
```

That path is chosen to match how the packaged runtime is imported and used at runtime. This fixed the earlier `kernel32.dll` startup failure caused by building against `/opt/wine`.

### No donor overlay

The workflow no longer contains any donor or kernel compatibility overlay step. The build path is now single-mode and deterministic.

## Packaging Outputs

### GameNative package

- Filename pattern: `proton-proton_11-YYYYMMDD-HASH-arm64ec.wcp`
- Compression: Zstandard
- Profile type: `Proton`

### Compatibility package

- Filename pattern: `proton-wine-proton-proton_11-YYYYMMDD-HASH-arm64ec.wcp.xz`
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

- use Valve Proton `proton_11.0` and initialize the `wine/` submodule
- use GameNative `proton_10.0`
- keep the internal profile version and baked install path aligned

If you change the internal profile version, update both:

- `PROFILE_VERSION`
- baked `INSTALL_DIR`

Those must continue to point at the same `/opt/proton-*` directory.

## Testing Priorities

1. Confirm the package imports
2. Confirm the runtime launches from `/opt/proton-11`
3. Confirm there is no fallback to `/opt/wine`
4. Confirm there is no `could not load kernel32.dll`
5. Only then debug game-specific runtime failures
