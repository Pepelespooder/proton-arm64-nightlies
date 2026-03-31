#!/bin/bash
# apply_patch_series.sh
# Apply a list of repo-owned patches to a Wine source checkout with
# already-applied detection and a few fallback strategies.
#
# Usage:
#   ./apply_patch_series.sh <wine-source-dir> <patch1> [patch2 ...]

set -euo pipefail

SOURCE_DIR="${1:-}"
shift || true

if [[ -z "$SOURCE_DIR" || ! -d "$SOURCE_DIR" ]]; then
    echo "Usage: $0 <wine-source-dir> <patch1> [patch2 ...]" >&2
    exit 1
fi

if [[ $# -eq 0 ]]; then
    echo "No patches specified; nothing to do."
    exit 0
fi

if [[ ! -d "$SOURCE_DIR/.git" ]]; then
    echo "ERROR: $SOURCE_DIR is not a git checkout" >&2
    exit 1
fi

apply_one() {
    local patch_path="$1"
    local patch_name
    patch_name="$(basename "$patch_path")"

    [[ -f "$patch_path" ]] || {
        echo "ERROR: patch not found: $patch_path" >&2
        exit 1
    }

    if git -C "$SOURCE_DIR" apply --ignore-whitespace -C1 -R --check "$patch_path" >/dev/null 2>&1; then
        echo "Patch already present: $patch_name"
        return 0
    fi

    if git -C "$SOURCE_DIR" apply --ignore-whitespace -C1 --check "$patch_path" >/dev/null 2>&1; then
        git -C "$SOURCE_DIR" apply --ignore-whitespace -C1 "$patch_path"
        echo "Applied patch: $patch_name"
        return 0
    fi

    if git -C "$SOURCE_DIR" apply --3way --ignore-space-change "$patch_path" >/dev/null 2>&1; then
        echo "Applied patch with 3-way merge: $patch_name"
        return 0
    fi

    if patch -d "$SOURCE_DIR" -p1 --forward --batch --ignore-whitespace -i "$patch_path" >/dev/null 2>&1; then
        echo "Applied patch with patch(1): $patch_name"
        return 0
    fi

    echo "ERROR: failed to apply patch: $patch_name" >&2
    exit 1
}

for patch_path in "$@"; do
    apply_one "$patch_path"
done
