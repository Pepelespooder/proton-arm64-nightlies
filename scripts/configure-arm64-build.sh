#!/bin/bash
# configure-arm64-build.sh
# Configure Wine/Proton for ARM64 Android (Winlator) cross-compilation.
#
# This script sets up the build environment using the Android NDK.
# NOTE: This targets Android ARM64 (bionic), NOT Valve's Steam Runtime ARM64.
#
# Usage:
#   ./configure-arm64-build.sh [--ndk-path <path>] [--source-dir <path>] [--build-dir <path>]
#
# Environment variables:
#   ANDROID_NDK_HOME  Path to Android NDK (required if --ndk-path not given)
#   WINE_SOURCE_DIR   Path to Wine source (default: ./wine-source)
#   BUILD_DIR         Path to build output (default: ./wine-build)

set -euo pipefail

# --- Defaults ---
NDK_PATH="${ANDROID_NDK_HOME:-}"
SOURCE_DIR="${WINE_SOURCE_DIR:-./wine-source}"
BUILD_DIR="${BUILD_DIR:-./wine-build}"
ANDROID_API=28
BUILD_NAME="proton-11-nightly-arm64ec"
PROFILE_VERSION="${PROFILE_VERSION:-11}"

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ndk-path)    NDK_PATH="$2";    shift 2 ;;
        --source-dir)  SOURCE_DIR="$2";  shift 2 ;;
        --build-dir)   BUILD_DIR="$2";   shift 2 ;;
        --api)         ANDROID_API="$2"; shift 2 ;;
        --name)        BUILD_NAME="$2";  shift 2 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# --- Validate NDK ---
if [[ -z "$NDK_PATH" ]]; then
    echo "Error: Android NDK path not specified."
    echo "Set ANDROID_NDK_HOME or use --ndk-path <path>"
    echo ""
    echo "Download NDK r27c:"
    echo "  curl -LO https://dl.google.com/android/repository/android-ndk-r27c-linux.zip"
    echo "  unzip android-ndk-r27c-linux.zip"
    exit 1
fi

if [[ ! -d "$NDK_PATH" ]]; then
    echo "Error: NDK directory not found: $NDK_PATH"
    exit 1
fi

TOOLCHAIN="$NDK_PATH/toolchains/llvm/prebuilt/linux-x86_64/bin"
if [[ ! -d "$TOOLCHAIN" ]]; then
    echo "Error: NDK toolchain not found at $TOOLCHAIN"
    exit 1
fi

# --- Set up cross-compilation environment ---
TARGET="aarch64-linux-android${ANDROID_API}"
CC="${TOOLCHAIN}/${TARGET}-clang"
CXX="${TOOLCHAIN}/${TARGET}-clang++"
AR="${TOOLCHAIN}/llvm-ar"
STRIP="${TOOLCHAIN}/llvm-strip"

echo "=== ARM64 Android Build Configuration ==="
echo "NDK path:    $NDK_PATH"
echo "Toolchain:   $TOOLCHAIN"
echo "Target:      $TARGET"
echo "CC:          $CC"
echo "Source dir:  $SOURCE_DIR"
echo "Build dir:   $BUILD_DIR"
echo "Android API: $ANDROID_API"
echo ""

# Verify compiler exists
if [[ ! -f "$CC" ]]; then
    echo "Error: Compiler not found: $CC"
    echo "Check that NDK r27+ is installed correctly."
    exit 1
fi
echo "[OK] Compiler found: $CC"
echo "     Version: $($CC --version | head -1)"

# --- Validate source ---
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "Error: Wine source directory not found: $SOURCE_DIR"
    echo "Clone the source first (see docs/BUILD_REQUIREMENTS.md)."
    exit 1
fi

if [[ ! -f "$SOURCE_DIR/configure" ]]; then
    echo "Error: configure script not found in $SOURCE_DIR"
    echo "The source may be incomplete or need to run autoreconf."
    exit 1
fi

# --- Create build directories ---
mkdir -p "$BUILD_DIR/tools"  # For host wine-tools (needed for cross-compile)
mkdir -p "$BUILD_DIR/target"

# --- Step 1: Build wine-tools (host native) ---
# Wine cross-compilation requires a native host build of wine tools first.
echo ""
echo "[1/2] Configuring host wine-tools (required for cross-compilation)..."
echo "      This builds native x86_64 tools needed by the cross-compile step."

HOST_TOOLS_DIR="$BUILD_DIR/tools"
(
    cd "$HOST_TOOLS_DIR"
    "$SOURCE_DIR/configure" \
        --enable-win64 \
        --without-x \
        --without-freetype \
        2>&1 | tee configure-tools.log
)
echo "      Host tools configured. Run 'make __tooldeps__' in $HOST_TOOLS_DIR first."

# --- Step 2: Configure target (ARM64 Android) ---
echo ""
echo "[2/2] Configuring ARM64 Android target..."

TARGET_BUILD_DIR="$BUILD_DIR/target"
(
    cd "$TARGET_BUILD_DIR"
    "$SOURCE_DIR/configure" \
        --host=aarch64-linux-android \
        --with-wine-tools="$HOST_TOOLS_DIR" \
        --prefix="/data/data/app.gamenative/files/imagefs/opt/proton-${PROFILE_VERSION}" \
        --bindir=bin \
        --libdir=lib \
        --enable-archs=aarch64,i386 \
        --without-x \
        --without-freetype \
        --without-dbus \
        --without-openldap \
        --without-sane \
        --without-netapi \
        CC="$CC" \
        CXX="$CXX" \
        AR="$AR" \
        STRIP="$STRIP" \
        TARGETCC="$CC" \
        TARGETCXX="$CXX" \
        CFLAGS="-O2 -DANDROID -fPIC" \
        LDFLAGS="-Wl,--build-id=sha1" \
        2>&1 | tee configure-target.log
)

echo ""
echo "Configuration complete."
echo ""
echo "Next steps:"
echo "  1. Build host tools:  make -C $HOST_TOOLS_DIR __tooldeps__"
echo "  2. Build Wine:        make -C $TARGET_BUILD_DIR"
echo "  3. Install:           make -C $TARGET_BUILD_DIR install DESTDIR=\$(pwd)/install"
echo "  4. Package:           ./scripts/package-proton-wcp.sh install/ output.wcp"
echo ""
echo "Or run the full automated build:"
echo "  ./scripts/build-proton-arm64.sh"
