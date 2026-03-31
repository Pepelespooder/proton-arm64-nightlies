#!/usr/bin/env python3
"""
Remove generated server file hunks from imported ntsync patches.

These files are regenerated from server/protocol.def during the build, and
they drift frequently enough on bleeding-edge that patching them directly is
fragile. Keeping protocol.def and the hand-written sources is enough.
"""
from __future__ import annotations

import sys
from pathlib import Path


DROP_PATHS = {
    "include/wine/server_protocol.h",
    "server/request_handlers.h",
    "server/request_trace.h",
}


def split_sections(text: str) -> list[str]:
    marker = "diff --git "
    start = text.find(marker)
    if start < 0:
        return [text]

    sections = [text[:start]]
    while start < len(text):
        nxt = text.find("\ndiff --git ", start + 1)
        if nxt < 0:
            sections.append(text[start:])
            break
        sections.append(text[start : nxt + 1])
        start = nxt + 1
    return sections


def section_path(section: str) -> str | None:
    first_line = section.splitlines()[0] if section.splitlines() else ""
    prefix = "diff --git a/"
    mid = " b/"
    if not first_line.startswith(prefix) or mid not in first_line:
        return None
    return first_line[len(prefix) : first_line.index(mid)]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: strip_generated_ntsync_patch_sections.py <patch> [patch ...]")
        return 1

    for arg in sys.argv[1:]:
        path = Path(arg)
        text = path.read_text(encoding="utf-8")
        sections = split_sections(text)

        kept = [sections[0]]
        removed = []
        for section in sections[1:]:
            rel = section_path(section)
            if rel in DROP_PATHS:
                removed.append(rel)
                continue
            kept.append(section)

        if removed:
            path.write_text("".join(kept), encoding="utf-8", newline="\n")
            print(f"Sanitized {path}: removed generated hunks for {', '.join(removed)}")
        else:
            print(f"No generated hunks removed from {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
