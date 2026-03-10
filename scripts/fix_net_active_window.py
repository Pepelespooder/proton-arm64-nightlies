#!/usr/bin/env python3
import os
import sys


def replace_once(src, old, new, description):
    if new in src:
        print(f"  [{description}] already applied, skipping")
        return src, 0
    if old not in src:
        print(f"  [{description}] pattern not found, skipping")
        return src, 0
    print(f"  [{description}] applied")
    return src.replace(old, new, 1), 1


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_net_active_window.py <wine-source-dir>")
        return 1

    event_c = os.path.join(os.path.abspath(sys.argv[1]), 'dlls', 'winex11.drv', 'event.c')
    if not os.path.exists(event_c):
        print(f"ERROR: {event_c} not found")
        return 1

    with open(event_c, encoding='utf-8', errors='replace') as f:
        src = f.read()

    total = 0
    replacements = [
        (
            'set_focus net active window fallback',
            '    if (X11DRV_HasWindowManager( "steamcompmgr" ) || !is_net_supported( x11drv_atom(_NET_ACTIVE_WINDOW) ))\n',
            '    if (!is_net_supported( x11drv_atom(_NET_ACTIVE_WINDOW) ))\n',
        ),
        (
            'focus_out net active window fallback',
            '    if ((X11DRV_HasWindowManager( "steamcompmgr" ) || !is_net_supported( x11drv_atom(_NET_ACTIVE_WINDOW) ))\n            && !is_current_process_focused())\n',
            '    if (!is_net_supported( x11drv_atom(_NET_ACTIVE_WINDOW) ) && !is_current_process_focused())\n',
        ),
    ]

    for description, old, new in replacements:
        src, n = replace_once(src, old, new, description)
        total += n

    with open(event_c, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)

    print(f"Done. Applied {total} net active window fix(es)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
