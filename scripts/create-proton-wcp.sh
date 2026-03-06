#!/bin/bash
# create-proton-wcp.sh
# Package a Proton/Wine Android build directory into a .wcp file for Winlator.
#
# Usage:
#   ./create-proton-wcp.sh <input_dir> <output.wcp> [version_name] [version_code] [description]
#
# Arguments:
#   input_dir    Directory containing: bin/ lib/ share/ prefixPack.txz (profile.json is always regenerated)
#   output.wcp   Output .wcp file path
#   version_name Optional: version string (default: derived from git or date)
#   version_code Optional: integer version code (default: YYYYMMDD)
#   description  Optional: description string
#
# Requirements:
#   - zstd binary OR python3 with zstandard module
#   - tar (GNU)
#
# Example:
#   ./create-proton-wcp.sh ./build/proton-output proton-10-nightly-20260305.wcp \
#     "10-arm64ec-nightly-20260305" 100020260305 "Proton 10 nightly ARM64 build"

set -euo pipefail

# --- Argument parsing ---
INPUT_DIR="${1:-}"
OUTPUT_WCP="${2:-}"
VERSION_NAME="${3:-}"
VERSION_CODE="${4:-}"
DESCRIPTION="${5:-}"

if [[ -z "$INPUT_DIR" || -z "$OUTPUT_WCP" ]]; then
    echo "Usage: $0 <input_dir> <output.wcp> [version_name] [version_code] [description]"
    exit 1
fi

if [[ ! -d "$INPUT_DIR" ]]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist."
    exit 1
fi

INPUT_DIR="$(cd "$INPUT_DIR" && pwd)"
OUTPUT_WCP="$(realpath -m "$OUTPUT_WCP")"

# --- Validate required contents ---
echo "[1/6] Validating input directory structure..."

MISSING=0
for required in bin lib share prefixPack.txz; do
    if [[ ! -e "$INPUT_DIR/$required" ]]; then
        echo "  WARNING: Missing expected item: $required"
        MISSING=$((MISSING + 1))
    fi
done

# --- Default version info from git or date ---
DATE_TAG="$(date -u +%Y%m%d)"

if [[ -z "$VERSION_NAME" ]]; then
    if git -C "$INPUT_DIR" rev-parse --short HEAD 2>/dev/null; then
        GIT_HASH="$(git -C "$INPUT_DIR" rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
        VERSION_NAME="10-arm64ec-nightly-${DATE_TAG}-${GIT_HASH}"
    else
        VERSION_NAME="10-arm64ec-nightly-${DATE_TAG}"
    fi
fi

if [[ -z "$VERSION_CODE" ]]; then
    VERSION_CODE="${DATE_TAG}"
fi

if [[ -z "$DESCRIPTION" ]]; then
    DESCRIPTION="Proton 10 ARM64 nightly build (${DATE_TAG})"
fi

echo "  Version name: $VERSION_NAME"
echo "  Version code: $VERSION_CODE"
echo "  Description:  $DESCRIPTION"

# --- Always regenerate profile.json ---
echo "[2/6] Generating profile.json..."

cat > "$INPUT_DIR/profile.json" << EOF
{
  "type": "Proton",
  "versionName": "${VERSION_NAME}",
  "versionCode": ${VERSION_CODE},
  "description": "${DESCRIPTION}",
  "files": [],
  "wine": {
    "binPath": "bin",
    "libPath": "lib",
    "prefixPack": "prefixPack.txz"
  }
}
EOF
echo "  Generated profile.json"

# --- Check compression tools ---
echo "[3/6] Checking available compression tools..."

USE_PYTHON=0
if command -v zstd &>/dev/null; then
    ZSTD_BIN="$(command -v zstd)"
    echo "  Found zstd: $ZSTD_BIN"
elif python3 -c "import zstandard" 2>/dev/null; then
    USE_PYTHON=1
    echo "  No zstd binary found; using Python zstandard module"
else
    echo "Error: Neither zstd binary nor Python zstandard module available."
    echo "Install one of:"
    echo "  sudo apt-get install zstd"
    echo "  pip3 install zstandard"
    exit 1
fi

# --- Create staging area ---
echo "[4/6] Preparing staging area..."

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

# Copy contents (not the directory itself) into staging
cp -r "$INPUT_DIR/." "$STAGING_DIR/"

# --- Create tar ---
echo "[5/6] Creating tar archive..."

TAR_FILE="$(mktemp --suffix=.tar)"
trap 'rm -rf "$STAGING_DIR" "$TAR_FILE"' EXIT

tar -cf "$TAR_FILE" -C "$STAGING_DIR" .
TAR_SIZE="$(du -sh "$TAR_FILE" | cut -f1)"
echo "  Tar archive size: $TAR_SIZE"

# --- Compress with zstd ---
echo "[6/6] Compressing with Zstandard..."

OUTPUT_DIR="$(dirname "$OUTPUT_WCP")"
mkdir -p "$OUTPUT_DIR"

if [[ $USE_PYTHON -eq 0 ]]; then
    # Use zstd binary: level 19 (max), multi-threaded
    zstd -T0 -19 --force -o "$OUTPUT_WCP" "$TAR_FILE"
else
    # Use Python zstandard
    python3 << PYEOF
import zstandard, sys, os

tar_path = "$TAR_FILE"
out_path = "$OUTPUT_WCP"

cctx = zstandard.ZstdCompressor(level=19, threads=-1)
with open(tar_path, 'rb') as src, open(out_path, 'wb') as dst:
    cctx.copy_stream(src, dst)

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"  Written {size_mb:.1f} MB to {out_path}")
PYEOF
fi

WCP_SIZE="$(du -sh "$OUTPUT_WCP" | cut -f1)"
echo "  Output: $OUTPUT_WCP ($WCP_SIZE)"

# --- Generate checksum ---
sha256sum "$OUTPUT_WCP" > "${OUTPUT_WCP}.sha256"
echo "  SHA256: $(cat "${OUTPUT_WCP}.sha256" | cut -d' ' -f1)"

echo ""
echo "Done. Package created: $OUTPUT_WCP"
echo "Checksum file:         ${OUTPUT_WCP}.sha256"

