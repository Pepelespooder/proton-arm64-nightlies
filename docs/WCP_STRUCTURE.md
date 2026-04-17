# .wcp File Format Documentation

## Overview

This repo currently produces two package formats:

- `.wcp`: Zstandard-compressed tar archive
- `.wcp.xz`: XZ-compressed tar archive

The main GameNative Proton artifact is the Zstandard `.wcp`. The `.wcp.xz` variant exists for compatibility with Ludashi/CMOD-style consumers.

## Archive Formats

```text
.wcp    = tar compressed with Zstandard
.wcp.xz = tar compressed with XZ
```

## Common Contents

Both package variants contain the same staged runtime layout:

```text
./
├── profile.json
├── prefixPack.txz
├── bin/
├── lib/
└── share/
```

## Current GameNative Metadata

Example current Proton metadata:

```json
{
  "type": "proton",
  "versionName": "11",
  "versionCode": 1,
  "description": "Proton_11 ARM64 20260307 (abcdef0)",
  "files": [],
  "wine": {
    "binPath": "bin",
    "libPath": "lib",
    "prefixPack": "prefixPack.txz"
  }
}
```

## Why `versionName` Is Numeric

The external `.wcp` naming uses `proton-proton_11`, and the internal `versionName` stays numeric so stock GameNative recognizes the package as ARM64EC Proton.

That internal value currently drives installation to:

```text
/opt/proton-11
```

## Packaging Commands

### Main Proton package

```bash
tar -cf - . | zstd -T0 -19 -o output.wcp
```

### Compatibility package

```bash
tar cJf output.wcp.xz bin lib share prefixPack.txz profile.json
```
