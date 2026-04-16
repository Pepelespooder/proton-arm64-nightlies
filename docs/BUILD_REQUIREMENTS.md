# Build Requirements for Proton ARM64 Proton 11 Builds

## Build Target

This repo builds Android-targeted Wine/Proton for ARM64. It is not desktop Proton.

Current assumptions:

- Android NDK r27d
- Android API 28 target
- Android/bionic runtime
- llvm-mingw for PE and ARM64EC pieces

## Source Requirements

- `ValveSoftware/Proton` at `proton_11.0`, with its `wine/` submodule initialized
- `GameNative/proton-wine` at `proton_10.0`

## Host Requirements

- Linux x86_64
- 8 GB RAM minimum, 16 GB recommended
- roughly 40 GB free disk recommended for comfortable builds

## Required Packages

Typical Ubuntu host packages:

```bash
sudo apt-get install -y \
  build-essential git wget curl unzip flex bison gettext autoconf automake \
  libtool pkg-config mingw-w64 gcc-multilib g++-multilib \
  libfreetype6-dev libpng-dev zlib1g-dev zstd xz-utils \
  python3-zstandard patch
```

The workflow also installs the i386 variants of some development libraries.

## Important Constraints

### Not desktop Proton

Do not use Valve's desktop Proton SDK assumptions here. This is an Android/bionic build.

### Patch stack required

The Proton `wine/` submodule alone is not enough. The build depends on the GameNative Android and ARM64EC patch stack plus the local fix scripts in this repo.

### Profile naming matters

If you want stock GameNative compatibility without an app-side parser change, keep the internal profile version numeric. The current workflow uses:

```text
11
```

### Install path must match

The build bakes its install path to:

```text
/data/data/com.winlator.cmod/files/imagefs/opt/proton-11
```

If you change the internal profile version, update the baked install path too.
