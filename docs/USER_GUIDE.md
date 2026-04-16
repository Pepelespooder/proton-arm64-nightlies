# User Guide: Proton ARM64 Bleeding-Edge Builds

## What These Builds Are

These are automated Proton ARM64 builds for Android, intended primarily for GameNative. They are built from Valve's `proton_11.0` Proton branch using its `wine/` submodule, then patched with GameNative's Android and ARM64EC changes.

There are two package variants:

- `proton-*.wcp` for GameNative
- `proton-wine-*.wcp.xz` for Ludashi/CMOD-style imports

## Requirements

- ARM64 Android device
- GameNative, or another compatible Winlator-derived app
- About 500 MB free for the downloaded package
- About 2-3 GB free for the imported runtime

## Downloading

1. Open the repository's **Releases** page
2. Find the latest release tagged `proton_11-YYYYMMDD-HASH`
3. Download:
   - `proton-*.wcp` for GameNative
   - `proton-wine-*.wcp.xz` for Ludashi/CMOD
4. Optionally download the matching `.sha256` file

## Verifying the Download

```bash
# Linux/macOS
sha256sum -c proton-proton_11-20260305-abc1234-arm64ec.wcp.sha256

# Windows PowerShell
Get-FileHash proton-proton_11-20260305-abc1234-arm64ec.wcp -Algorithm SHA256
```

## Installing in GameNative

1. Copy the `.wcp` file to the device
2. Open GameNative
3. Go to the Wine/Proton import screen
4. Select the downloaded `.wcp`
5. Wait for import to finish
6. Select the imported version in the container settings

## Important Compatibility Note

The visible release naming uses `proton_11`, and the internal profile version is simply `11`.

That is intentional. Stock GameNative's existing parser only recognizes ARM64EC Proton if the internal version stays numeric.

## Common Problems

**The imported version does not appear**

- Make sure you used the `.wcp` artifact for GameNative
- Restart the app after import
- Confirm the download finished correctly

**The app rejects the file**

- Use `.wcp` for GameNative
- Use `.wcp.xz` only for Ludashi/CMOD-style imports

**A game crashes after startup**

- That is now a game/runtime issue, not a packaging bootstrap issue
- Collect logcat and include the release tag when reporting it

## Reporting Problems

Include:

- Release tag
- Exact artifact filename
- Device model
- Android version
- App name and version
- Game name
- Relevant logs

## Rolling Back

Older builds remain in GitHub Releases. Download the earlier artifact you want and re-import it.
