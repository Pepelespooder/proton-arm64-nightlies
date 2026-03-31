#!/bin/bash
# build-proton-arm64.sh
# Full automated build of Wine/Proton for ARM64 Android (Winlator).
#
# Usage:
#   ./build-proton-arm64.sh [options]
#
# Options:
#   --ndk-path <path>     Android NDK path (or set ANDROID_NDK_HOME)
#   --source-dir <path>   Wine source directory (default: ./wine-source)
#   --build-dir <path>    Build output directory (default: ./wine-build)
#   --jobs <n>            Parallel jobs (default: nproc)
#   --skip-configure      Skip configure step (resume build)
#   --skip-tools          Skip host tools build (if already built)
#   --enable-ntsync       Apply the optional ntsync patch series
#   --clean               Clean build directory before starting
#
# Environment variables:
#   ANDROID_NDK_HOME      Android NDK root
#   CCACHE_DIR            ccache directory (enables ccache if set)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_START_TIME="$(date -u +%s)"

# --- Defaults ---
NDK_PATH="${ANDROID_NDK_HOME:-}"
SOURCE_DIR="${WINE_SOURCE_DIR:-$(dirname "$SCRIPT_DIR")/wine-source}"
BUILD_DIR="${BUILD_DIR:-$(dirname "$SCRIPT_DIR")/wine-build}"
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 4)}"
SKIP_CONFIGURE=0
SKIP_TOOLS=0
CLEAN_BUILD=0
ENABLE_NTSYNC=0
ANDROID_API=28
PROFILE_VERSION="${PROFILE_VERSION:-10.0.99-arm64ec}"
PROFILE_VERSION_CODE="${PROFILE_VERSION_CODE:-1}"

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ndk-path)       NDK_PATH="$2";      shift 2 ;;
        --source-dir)     SOURCE_DIR="$2";    shift 2 ;;
        --build-dir)      BUILD_DIR="$2";     shift 2 ;;
        --jobs)           JOBS="$2";          shift 2 ;;
        --skip-configure) SKIP_CONFIGURE=1;   shift ;;
        --skip-tools)     SKIP_TOOLS=1;       shift ;;
        --enable-ntsync)  ENABLE_NTSYNC=1;    shift ;;
        --clean)          CLEAN_BUILD=1;      shift ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# --- Logging ---
LOG_DIR="$BUILD_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/build-$(date -u +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

log() { echo "[$(date -u +%H:%M:%S)] $*"; }
die() { log "ERROR: $*"; exit 1; }

log "=== Proton ARM64 Android Build ==="
log "Build started: $(date -u)"
log "Jobs: $JOBS"
log "Log: $LOG_FILE"

# --- Disk space check ---
AVAILABLE_GB="$(df -BG "$BUILD_DIR/../" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G' || echo 0)"
log "Available disk: ${AVAILABLE_GB}GB"
if [[ "$AVAILABLE_GB" -lt 30 ]]; then
    log "WARNING: Less than 30GB available. Build may fail due to disk space."
fi

# --- NDK validation ---
if [[ -z "$NDK_PATH" ]]; then
    die "ANDROID_NDK_HOME not set. Use --ndk-path or export ANDROID_NDK_HOME."
fi
[[ -d "$NDK_PATH" ]] || die "NDK directory not found: $NDK_PATH"

TOOLCHAIN="$NDK_PATH/toolchains/llvm/prebuilt/linux-x86_64/bin"
TARGET="aarch64-linux-android${ANDROID_API}"
CC="${TOOLCHAIN}/${TARGET}-clang"
CXX="${TOOLCHAIN}/${TARGET}-clang++"
AR="${TOOLCHAIN}/llvm-ar"
STRIP="${TOOLCHAIN}/llvm-strip"

[[ -f "$CC" ]] || die "Compiler not found: $CC"
log "Compiler: $($CC --version | head -1)"

# --- ccache setup ---
if [[ -n "${CCACHE_DIR:-}" ]] && command -v ccache &>/dev/null; then
    log "ccache enabled: $CCACHE_DIR"
    CC="ccache $CC"
    CXX="ccache $CXX"
fi

# --- Source validation ---
[[ -d "$SOURCE_DIR" ]] || die "Wine source not found: $SOURCE_DIR. Run: git clone <wine-android-repo> $SOURCE_DIR"
[[ -f "$SOURCE_DIR/configure" ]] || die "configure not found in $SOURCE_DIR"

# Keep local builds aligned with the workflow patch set for Winlator container exit.
"$SCRIPT_DIR/apply_patch_series.sh" \
    "$SOURCE_DIR" \
    "$SCRIPT_DIR/../patches/ge-gamenative-firstpass/explorer/explorer_startmenu_shutdown_latch.patch"

if [[ $ENABLE_NTSYNC -eq 1 ]]; then
    log "Applying optional ntsync patch series"
    "$SCRIPT_DIR/apply_patch_series.sh" \
        "$SOURCE_DIR" \
        "$SCRIPT_DIR/../patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0162-ntdll-Add-stub-functions-for-in-process-synchronizat.patch" \
        "$SCRIPT_DIR/../patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0163-ntdll-Retrieve-and-cache-an-ntsync-device-in-wait-ca.patch" \
        "$SCRIPT_DIR/../patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0164-server-Add-an-object-operation-to-retrieve-an-in-pro.patch" \
        "$SCRIPT_DIR/../patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0165-ntsync-implementation.patch" \
        "$SCRIPT_DIR/../patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0166-Finish-up-ntsync-console-implementation.patch" \
        "$SCRIPT_DIR/../patches/ge-wine-only-wrapper/patches/wine-hotfixes/wine-wayland/0172-ntdll-ntsync-remove-unused-variable-fix-datatypes.patch"
    python3 "$SCRIPT_DIR/fix_ntsync.py" "$SOURCE_DIR"
fi

# --- Clean if requested ---
if [[ $CLEAN_BUILD -eq 1 ]]; then
    log "Cleaning build directory: $BUILD_DIR"
    rm -rf "$BUILD_DIR/host" "$BUILD_DIR/target" "$BUILD_DIR/install"
fi

mkdir -p "$BUILD_DIR/host" "$BUILD_DIR/target" "$BUILD_DIR/install"

# --- Git info ---
GIT_HASH="unknown"
GIT_DATE="$(date -u +%Y%m%d)"
if git -C "$SOURCE_DIR" rev-parse HEAD &>/dev/null; then
    GIT_HASH="$(git -C "$SOURCE_DIR" rev-parse --short HEAD)"
    GIT_DATE="$(git -C "$SOURCE_DIR" log -1 --format='%cd' --date=format:'%Y%m%d')"
fi
ARTIFACT_VERSION="proton-bleeding-edge-${GIT_DATE}-${GIT_HASH}-arm64ec"
DISPLAY_NAME="Proton bleeding-edge ARM64EC ${GIT_DATE} (${GIT_HASH})"
log "Artifact version: $ARTIFACT_VERSION"
log "Profile version:  $PROFILE_VERSION"

# ============================================================
# STEP 1: Configure host tools
# ============================================================
if [[ $SKIP_CONFIGURE -eq 0 && $SKIP_TOOLS -eq 0 ]]; then
    log ""
    log "--- Step 1: Prepare Wine build system (make_requests etc.) ---"
    (
        cd "$SOURCE_DIR"
        ./tools/make_requests
        ./tools/make_specfiles
        ./tools/make_makefiles
        autoreconf -f
    )

    log "--- Step 1b: Configure host wine-tools ---"
    (
        cd "$BUILD_DIR/host"
        env -u CC -u CXX "$SOURCE_DIR/configure" \
            --enable-win64 \
            --without-x \
            --without-freetype \
            --without-gnutls \
            --without-unwind \
            --without-pulse \
            --without-gstreamer \
            --without-alsa \
            --without-sdl \
            --without-vulkan \
            --without-cups \
            --without-krb5 \
            --without-netapi \
            --without-gphoto \
            --without-udev \
            --without-capi \
            --without-ffmpeg \
            2>&1
    )
    log "Host tools configured."
fi

# ============================================================
# STEP 2: Build host tools
# ============================================================
if [[ $SKIP_TOOLS -eq 0 ]]; then
    log ""
    log "--- Step 2: Build host wine-tools ---"
    TOOLS_START="$(date -u +%s)"
    # __tooldeps__ builds everything under tools/ and tools/*/ at once.
    # This is the Wine 9+ replacement for the removed __builtin__ target.
    make -C "$BUILD_DIR/host" -j"$JOBS" __tooldeps__
    TOOLS_TIME=$(( $(date -u +%s) - TOOLS_START ))
    log "Host tools built in ${TOOLS_TIME}s"
fi

# ============================================================
# STEP 3: Configure ARM64 target
# ============================================================
if [[ $SKIP_CONFIGURE -eq 0 ]]; then
    log ""
    log "--- Step 3: Configure ARM64 Android target ---"
    (
        cd "$BUILD_DIR/target"
        APP_ID="${WINLATOR_APP_ID:-app.gamenative}"
        PREFIX="/data/data/${APP_ID}/files/imagefs/opt/proton-${PROFILE_VERSION}"
        "$SOURCE_DIR/configure" \
            --host=aarch64-linux-android \
            --with-wine-tools="$BUILD_DIR/host" \
            --prefix="$PREFIX" \
            --bindir="$PREFIX/bin" \
            --libdir="$PREFIX/lib" \
            --enable-archs=aarch64,i386 \
            --without-x \
            --without-freetype \
            --without-gnutls \
            --without-unwind \
            --without-dbus \
            --without-sane \
            --without-netapi \
            --without-pulse \
            --without-gstreamer \
            --without-alsa \
            --without-sdl \
            --without-vulkan \
            --without-cups \
            --without-krb5 \
            --without-gphoto \
            --without-udev \
            --without-capi \
            --without-ffmpeg \
            CC="$CC" \
            CXX="$CXX" \
            AR="$AR" \
            STRIP="$STRIP" \
            TARGETCC="$CC" \
            TARGETCXX="$CXX" \
            CFLAGS="-O2 -DANDROID -fPIC" \
            LDFLAGS="-Wl,--build-id=sha1" \
            2>&1
    )
    log "ARM64 target configured."
fi

# ============================================================
# STEP 4: Build Wine
# ============================================================
log ""
log "--- Step 4: Build Wine ARM64 ---"
BUILD_WINE_START="$(date -u +%s)"
make -C "$BUILD_DIR/target" -j"$JOBS" 2>&1
BUILD_WINE_TIME=$(( $(date -u +%s) - BUILD_WINE_START ))
log "Wine built in ${BUILD_WINE_TIME}s ($(( BUILD_WINE_TIME / 60 ))m)"

# ============================================================
# STEP 5: Install to staging
# ============================================================
log ""
log "--- Step 5: Install to staging directory ---"
INSTALL_DIR="$BUILD_DIR/install"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
make -C "$BUILD_DIR/target" install DESTDIR="$INSTALL_DIR"

# Reorganize to match expected .wcp layout
# make install puts files under prefix; flatten to bin/ lib/ share/
APP_ID="${WINLATOR_APP_ID:-app.gamenative}"
WINE_PREFIX_INNER="$INSTALL_DIR/data/data/${APP_ID}/files/imagefs/opt/proton-${PROFILE_VERSION}"
if [[ -d "$WINE_PREFIX_INNER" ]]; then
    cp -r "$WINE_PREFIX_INNER/." "$INSTALL_DIR/"
    rm -rf "$INSTALL_DIR/data"
else
    die "Expected installed runtime at $WINE_PREFIX_INNER, but it was not found"
fi

log "Installed to: $INSTALL_DIR"
log "Contents:"
ls -lh "$INSTALL_DIR"

# ============================================================
# STEP 6: Verify runtime ABI
# ============================================================
log ""
log "--- Step 6: Verifying runtime ABI ---"
"$SCRIPT_DIR/verify-runtime-abi.sh" "$INSTALL_DIR"
log "ABI verification complete."

# ============================================================
# STEP 7: Strip binaries (reduce size)
# ============================================================
log ""
log "--- Step 7: Stripping debug symbols ---"
find "$INSTALL_DIR/lib/wine/aarch64-unix" -name "*.so" -exec "$STRIP" --strip-debug {} \;
"$STRIP" --strip-debug "$INSTALL_DIR/bin/wine" "$INSTALL_DIR/bin/wineserver" 2>/dev/null || true
log "Stripping complete."

# ============================================================
# STEP 8: Generate profile.json
# ============================================================
log ""
log "--- Step 8: Generating profile.json ---"
python3 "$SCRIPT_DIR/generate_profile.py" \
    "$INSTALL_DIR/profile.json" \
    "$PROFILE_VERSION" \
    "$PROFILE_VERSION_CODE" \
    "$DISPLAY_NAME"
log "profile.json written."

# ============================================================
# STEP 9: Copy prefixPack.txz
# ============================================================
log ""
log "--- Step 9: Adding prefixPack.txz ---"
REFERENCE_PREFIX="$(dirname "$SCRIPT_DIR")/reference/extracted/prefixPack.txz"
if [[ -f "$REFERENCE_PREFIX" ]]; then
    cp "$REFERENCE_PREFIX" "$INSTALL_DIR/prefixPack.txz"
    log "Copied prefixPack.txz from reference build."
else
    log "WARNING: prefixPack.txz not found at $REFERENCE_PREFIX"
    log "         The .wcp will be missing the default Wine prefix."
    log "         Copy a prefixPack.txz manually or generate one with wineboot."
fi

# ============================================================
# STEP 10: Package as .wcp
# ============================================================
log ""
log "--- Step 10: Packaging as .wcp ---"
OUTPUT_DIR="$(dirname "$SCRIPT_DIR")/output"
mkdir -p "$OUTPUT_DIR"
OUTPUT_WCP="$OUTPUT_DIR/proton-${ARTIFACT_VERSION}.wcp"

"$SCRIPT_DIR/create-proton-wcp.sh" \
    "$INSTALL_DIR" \
    "$OUTPUT_WCP" \
    "$PROFILE_VERSION" \
    "$PROFILE_VERSION_CODE" \
    "$DISPLAY_NAME"

# ============================================================
# Summary
# ============================================================
TOTAL_TIME=$(( $(date -u +%s) - BUILD_START_TIME ))
log ""
log "=== Build Complete ==="
log "Total time: ${TOTAL_TIME}s ($(( TOTAL_TIME / 60 ))m)"
log "Output:     $OUTPUT_WCP"
log "SHA256:     $(cat "${OUTPUT_WCP}.sha256" | cut -d' ' -f1)"
log "Size:       $(du -sh "$OUTPUT_WCP" | cut -f1)"


