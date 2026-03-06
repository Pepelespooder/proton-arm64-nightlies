#!/usr/bin/env python3
"""Normalize GameNative container wineVersion to canonical profile entry.

Usage:
  normalize_container_wineversion.py <container_json> <Type> <versionName> <versionCode>

Example:
  normalize_container_wineversion.py container.json Proton proton-10.0-nightly-abc-arm64ec 1
"""
import json
import pathlib
import sys


def main() -> int:
    if len(sys.argv) != 5:
        print("Usage: normalize_container_wineversion.py <container_json> <Type> <versionName> <versionCode>")
        return 1

    path = pathlib.Path(sys.argv[1])
    profile_type = sys.argv[2]
    version_name = sys.argv[3]
    try:
        version_code = int(sys.argv[4])
    except ValueError:
        print("ERROR: versionCode must be an integer")
        return 2

    if not path.exists():
        print(f"ERROR: missing container file: {path}")
        return 3

    original_text = path.read_text(encoding="utf-8")
    data = json.loads(original_text)

    canonical = f"{profile_type}-{version_name}-{version_code}"
    previous = data.get("wineVersion", "")
    data["wineVersion"] = canonical

    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(original_text, encoding="utf-8")

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Updated {path}")
    print(f"  old wineVersion: {previous}")
    print(f"  new wineVersion: {canonical}")
    print(f"  backup written : {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())