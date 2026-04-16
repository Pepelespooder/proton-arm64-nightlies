#!/bin/bash
# package-proton-wcp.sh
# End-to-end pipeline: take a Proton redist/install directory and produce a .wcp.
# This is the high-level wrapper that calls create-proton-wcp.sh with all options
# derived automatically from the build artifacts.
#
# Usage:
#   ./package-proton-wcp.sh <build_dir> [output_dir]
#
# Arguments:
#   build_dir   Directory containing Proton build output (bin/ lib/ share/)
#   output_dir  Where to write the .wcp file (default: ./output)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT_DIR="${1:-}"
OUTPUT_DIR="${2:-$(dirname "$SCRIPT_DIR")/output}"

if [[ -z "$INPUT_DIR" ]]; then
    echo "Usage: $0 <build_dir> [output_dir]"
    exit 1
fi

[[ -d "$INPUT_DIR" ]] || { echo "Error: Directory not found: $INPUT_DIR"; exit 1; }

INPUT_DIR="$(cd "$INPUT_DIR" && pwd)"
mkdir -p "$OUTPUT_DIR"

echo "=== Proton .wcp Packaging Pipeline ==="
echo "Input:      $INPUT_DIR"
echo "Output dir: $OUTPUT_DIR"

# --- Extract version info ---
DATE_TAG="$(date -u +%Y%m%d)"
GIT_HASH="unknown"

# Try to get git info from source dir
for dir in "$INPUT_DIR" "$(dirname "$SCRIPT_DIR")/wine-source" "."; do
    if git -C "$dir" rev-parse HEAD &>/dev/null 2>&1; then
        GIT_HASH="$(git -C "$dir" rev-parse --short HEAD 2>/dev/null)"
        DATE_TAG="$(git -C "$dir" log -1 --format='%cd' --date=format:'%Y%m%d' 2>/dev/null || echo "$DATE_TAG")"
        break
    fi
done

VERSION_NAME="11"
VERSION_CODE="1"
DESCRIPTION="Proton_11 ARM64EC ${DATE_TAG} (${GIT_HASH})"
OUTPUT_WCP="$OUTPUT_DIR/proton-proton_11-${DATE_TAG}-${GIT_HASH}-arm64ec.wcp"

echo "Version:    $VERSION_NAME"
echo "Output:     $OUTPUT_WCP"
echo ""

# --- Validate structure ---
echo "[1/4] Validating build output structure..."
ERRORS=0
for item in bin lib share; do
    if [[ -d "$INPUT_DIR/$item" ]]; then
        echo "  [OK] $item/"
    else
        echo "  [MISSING] $item/"
        ERRORS=$((ERRORS + 1))
    fi
done

for bin in bin/wine bin/wineserver; do
    if [[ -f "$INPUT_DIR/$bin" ]]; then
        echo "  [OK] $bin"
    else
        echo "  [MISSING] $bin"
        ERRORS=$((ERRORS + 1))
    fi
done

if [[ $ERRORS -gt 0 ]]; then
    echo ""
    echo "WARNING: $ERRORS required items missing. Proceeding anyway..."
fi

# --- Check for prefixPack.txz ---
echo ""
echo "[2/4] Checking for prefixPack.txz..."
if [[ ! -f "$INPUT_DIR/prefixPack.txz" ]]; then
    REFERENCE="$(dirname "$SCRIPT_DIR")/reference/extracted/prefixPack.txz"
    if [[ -f "$REFERENCE" ]]; then
        echo "  Copying from reference build..."
        cp "$REFERENCE" "$INPUT_DIR/prefixPack.txz"
    else
        echo "  WARNING: No prefixPack.txz available. Package may not work in Winlator."
    fi
else
    echo "  [OK] prefixPack.txz found"
fi

# --- Verify binaries are ARM64 Android ---
echo ""
echo "[3/4] Verifying binary architecture..."
if command -v file &>/dev/null && [[ -f "$INPUT_DIR/bin/wine" ]]; then
    WINE_FILE="$(file "$INPUT_DIR/bin/wine")"
    echo "  bin/wine: $WINE_FILE"
    if echo "$WINE_FILE" | grep -q "aarch64"; then
        echo "  [OK] ARM64 confirmed"
    else
        echo "  [WARNING] Expected ARM64 binary - got something else!"
    fi
fi

# --- Package ---
echo ""
echo "[4/4] Creating .wcp package..."
"$SCRIPT_DIR/create-proton-wcp.sh" \
    "$INPUT_DIR" \
    "$OUTPUT_WCP" \
    "$VERSION_NAME" \
    "$VERSION_CODE" \
    "$DESCRIPTION"

# --- Summary ---
echo ""
echo "=== Packaging Complete ==="
echo "Output: $OUTPUT_WCP"
echo "Size:   $(du -sh "$OUTPUT_WCP" | cut -f1)"
echo "SHA256: $(cat "${OUTPUT_WCP}.sha256" | cut -d' ' -f1)"
echo ""
echo "To install in Winlator:"
echo "  1. Copy $OUTPUT_WCP to your Android device"
echo "  2. In Winlator: Settings > Wine Version > Import > select the .wcp file"
