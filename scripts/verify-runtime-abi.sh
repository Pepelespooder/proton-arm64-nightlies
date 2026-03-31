#!/bin/bash
# verify-runtime-abi.sh
# Fail the build when staged Wine modules require shared-library SONAMEs that
# are known not to exist in the target Winlator imagefs.
#
# Usage:
#   ./verify-runtime-abi.sh <runtime-dir>
#
# Environment variables:
#   WINLATOR_APP_ID       Target app id. If set to com.winlator.cmod, CMOD v13
#                         ffmpeg SONAMEs are enforced by default.
#   ABI_EXPECT_LIBAVUTIL  Override expected ffmpeg SONAME for winedmo.so
#   ABI_EXPECT_LIBAVCODEC Override expected ffmpeg SONAME for winedmo.so
#   ABI_EXPECT_LIBAVFORMAT Override expected ffmpeg SONAME for winedmo.so

set -euo pipefail

RUNTIME_DIR="${1:-}"

if [[ -z "$RUNTIME_DIR" || ! -d "$RUNTIME_DIR" ]]; then
    echo "Usage: $0 <runtime-dir>" >&2
    exit 1
fi

if ! command -v readelf >/dev/null 2>&1; then
    echo "ERROR: readelf is required for ABI verification" >&2
    exit 1
fi

APP_ID="${WINLATOR_APP_ID:-app.gamenative}"
EXPECT_LIBAVUTIL="${ABI_EXPECT_LIBAVUTIL:-}"
EXPECT_LIBAVCODEC="${ABI_EXPECT_LIBAVCODEC:-}"
EXPECT_LIBAVFORMAT="${ABI_EXPECT_LIBAVFORMAT:-}"

if [[ -z "$EXPECT_LIBAVUTIL" && -z "$EXPECT_LIBAVCODEC" && -z "$EXPECT_LIBAVFORMAT" ]]; then
    case "$APP_ID" in
        com.winlator.cmod)
            EXPECT_LIBAVUTIL="libavutil.so.59"
            EXPECT_LIBAVCODEC="libavcodec.so.61"
            EXPECT_LIBAVFORMAT="libavformat.so.61"
            ;;
        *)
            echo "ABI check: no ffmpeg SONAME baseline configured for $APP_ID, skipping winedmo check"
            exit 0
            ;;
    esac
fi

MODULE_PATH="$(
    find "$RUNTIME_DIR" -type f \
        \( -name 'winedmo.so' -o -name 'winedmo.dll.so' -o -name 'winedmo.dll' \) \
        | head -n 1
)"

if [[ -z "$MODULE_PATH" ]]; then
    echo "ABI check: winedmo module not present in $RUNTIME_DIR, skipping ffmpeg SONAME check"
    exit 0
fi

mapfile -t NEEDED_LIBS < <(readelf -d "$MODULE_PATH" | sed -n 's/.*Shared library: \[\(.*\)\]/\1/p')

echo "ABI check: inspecting $MODULE_PATH"
printf 'ABI check: NEEDED => %s\n' "${NEEDED_LIBS[@]}"

require_exact_soname() {
    local expected="$1"
    local family_prefix="$2"
    local actual=""
    local lib

    for lib in "${NEEDED_LIBS[@]}"; do
        if [[ "$lib" == "${family_prefix}"* ]]; then
            actual="$lib"
            break
        fi
    done

    if [[ -z "$actual" ]]; then
        echo "ERROR: $MODULE_PATH does not declare any ${family_prefix}* dependency" >&2
        exit 1
    fi

    if [[ "$actual" != "$expected" ]]; then
        echo "ERROR: $MODULE_PATH requires $actual but target imagefs expects $expected" >&2
        exit 1
    fi
}

require_exact_soname "$EXPECT_LIBAVUTIL" "libavutil.so."
require_exact_soname "$EXPECT_LIBAVCODEC" "libavcodec.so."
require_exact_soname "$EXPECT_LIBAVFORMAT" "libavformat.so."

echo "ABI check: ffmpeg SONAMEs match the configured target baseline"
