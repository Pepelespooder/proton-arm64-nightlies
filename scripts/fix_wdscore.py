#!/usr/bin/env python3
import os
import re
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: fix_wdscore.py <wine-source-dir>")
        return 1

    wine_src = os.path.abspath(sys.argv[1])
    path = os.path.join(wine_src, "dlls", "wdscore", "wdscore.spec")

    if not os.path.exists(path):
        print(f"SKIP: {path} not found")
        return 0

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # Strip mangled C++ CDynamicArray exports/stubs that break ARM64EC linking.
    bad_patterns = [
        re.compile(r"CDynamicArray"),
        re.compile(r"\?\?"),      # MSVC-mangled C++ symbol
        re.compile(r"@QAE@|@QBE@|@IAE@|@AAV|@ABV|@@QAE|@@QBE"),
    ]

    kept = []
    removed = []

    for line in lines:
        if "CDynamicArray" in line and (
            "??" in line
            or "@QAE@" in line
            or "@QBE@" in line
            or "@IAE@" in line
            or "@AAV" in line
            or "@ABV" in line
            or "@@QAE" in line
            or "@@QBE" in line
        ):
            removed.append(line.rstrip("\n"))
            continue
        kept.append(line)

    if not removed:
        print("OK: no ARM64EC-invalid CDynamicArray stubs found in wdscore.spec")
        return 0

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(kept)

    print(f"FIXED: removed {len(removed)} bad wdscore.spec lines")
    for line in removed:
        print(f"  removed: {line}")

    # Verify cleanup
    remaining = []
    for line in kept:
        if "CDynamicArray" in line and (
            "??" in line
            or "@QAE@" in line
            or "@QBE@" in line
            or "@IAE@" in line
            or "@AAV" in line
            or "@ABV" in line
            or "@@QAE" in line
            or "@@QBE" in line
        ):
            remaining.append(line.rstrip("\n"))

    if remaining:
        print("ERROR: wdscore.spec still contains bad CDynamicArray entries")
        for line in remaining:
            print(f"  remaining: {line}")
        return 2

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
