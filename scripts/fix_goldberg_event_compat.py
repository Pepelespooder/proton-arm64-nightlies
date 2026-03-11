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
        print("Usage: fix_goldberg_event_compat.py <wine-source-dir>")
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
            'allow WM_TAKE_FOCUS during state changes on android',
            '        if (window_has_pending_wm_state( hwnd, -1 ) || (hwnd != foreground && !window_should_take_focus( foreground, event_time )))\n'
            '        {\n'
            '            WARN( "Ignoring window %p/%lx WM_TAKE_FOCUS serial %lu, event_time %ld, foreground %p during WM_STATE change\\n",\n'
            '                  hwnd, event->window, event->serial, event_time, foreground );\n'
            '            return;\n'
            '        }\n',
            '#ifdef __ANDROID__\n'
            '        if (hwnd != foreground && !window_should_take_focus( foreground, event_time ))\n'
            '#else\n'
            '        if (window_has_pending_wm_state( hwnd, -1 ) || (hwnd != foreground && !window_should_take_focus( foreground, event_time )))\n'
            '#endif\n'
            '        {\n'
            '            WARN( "Ignoring window %p/%lx WM_TAKE_FOCUS serial %lu, event_time %ld, foreground %p during WM_STATE change\\n",\n'
            '                  hwnd, event->window, event->serial, event_time, foreground );\n'
            '            return;\n'
            '        }\n',
        ),
        (
            'allow FocusIn during state changes on android',
            '    if (window_has_pending_wm_state( hwnd, -1 ))\n'
            '    {\n'
            '        WARN( "Ignoring window %p/%lx FocusIn serial %lu, detail %s, mode %s, foreground %p during WM_STATE change\\n",\n'
            '              hwnd, event->window, event->serial, focus_details[event->detail], focus_modes[event->mode], foreground );\n'
            '        return FALSE;\n'
            '    }\n\n',
            '#ifndef __ANDROID__\n'
            '    if (window_has_pending_wm_state( hwnd, -1 ))\n'
            '    {\n'
            '        WARN( "Ignoring window %p/%lx FocusIn serial %lu, detail %s, mode %s, foreground %p during WM_STATE change\\n",\n'
            '              hwnd, event->window, event->serial, focus_details[event->detail], focus_modes[event->mode], foreground );\n'
            '        return FALSE;\n'
            '    }\n'
            '#endif\n\n',
        ),
        (
            'preserve old focus_out fallback on android',
            '    if ((X11DRV_HasWindowManager( "steamcompmgr" ) || !is_net_supported( x11drv_atom(_NET_ACTIVE_WINDOW) ))\n'
            '            && !is_current_process_focused())\n',
            '#ifdef __ANDROID__\n'
            '    if (!is_current_process_focused())\n'
            '#else\n'
            '    if ((X11DRV_HasWindowManager( "steamcompmgr" ) || !is_net_supported( x11drv_atom(_NET_ACTIVE_WINDOW) ))\n'
            '            && !is_current_process_focused())\n'
            '#endif\n',
        ),
    ]

    for description, old, new in replacements:
        src, n = replace_once(src, old, new, description)
        total += n

    with open(event_c, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src)

    print(f"Done. Applied {total} Goldberg event compat fix(es)")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
