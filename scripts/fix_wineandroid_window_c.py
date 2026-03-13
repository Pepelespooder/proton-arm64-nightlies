#!/usr/bin/env python3
"""
Applies the Android relative-mouse bridge changes to dlls/wineandroid.drv/window.c
directly in the source tree.

This avoids relying on a drift-prone patch against bleeding-edge while keeping
the optional runtime toggle and logging available in the final build.

Usage: fix_wineandroid_window_c.py <wine-source-dir>
"""
import os
import re
import sys


def apply_literal(src, description, old, new):
    if new in src:
        print(f"  [{description}] already applied, skipping")
        return src, 0
    if old not in src:
        print(f"  [{description}] pattern not found, skipping")
        return src, 0
    print(f"  [{description}] applied")
    return src.replace(old, new, 1), 1


def apply_regex(src, description, pattern, replacement):
    if replacement in src:
        print(f"  [{description}] already applied, skipping")
        return src, 0
    new_src, count = re.subn(pattern, replacement, src, count=1, flags=re.S)
    if not count:
        print(f"  [{description}] pattern not found, skipping")
        return src, 0
    print(f"  [{description}] applied")
    return new_src, 1


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_wineandroid_window_c.py <wine-source-dir>")
        sys.exit(1)

    wine_src = sys.argv[1]
    window_c = os.path.join(wine_src, "dlls", "wineandroid.drv", "window.c")

    if not os.path.exists(window_c):
        print(f"ERROR: {window_c} not found")
        sys.exit(1)

    with open(window_c, encoding="utf-8", errors="replace") as f:
        src = f.read()

    total = 0

    src, n = apply_literal(
        src,
        "ntuser include",
        '#include "winuser.h"\n\n#include "android.h"\n',
        '#include "winuser.h"\n#include "ntuser.h"\n\n#include "android.h"\n',
    )
    total += n

    src, n = apply_literal(
        src,
        "relative mouse helpers",
        "static struct list event_queue = LIST_INIT( event_queue );\n"
        "static struct java_event *current_event;\n"
        "static int event_pipe[2];\n"
        "static DWORD desktop_tid;\n\n"
        "/***********************************************************************\n"
        " *           send_event\n"
        " */\n",
        "static struct list event_queue = LIST_INIT( event_queue );\n"
        "static struct java_event *current_event;\n"
        "static int event_pipe[2];\n"
        "static DWORD desktop_tid;\n\n"
        "static BOOL android_relative_mouse_enabled(void)\n"
        "{\n"
        '    const char *value = getenv( "WINE_ANDROID_RELATIVE_MOUSE" );\n'
        "    return value && atoi( value );\n"
        "}\n\n"
        "static BOOL android_input_debug_enabled(void)\n"
        "{\n"
        '    const char *value = getenv( "WINE_INPUT_POLL_DEBUG" );\n'
        "    return value && atoi( value );\n"
        "}\n\n"
        "static BOOL android_relative_mouse_active( HWND capture )\n"
        "{\n"
        "    RECT clip;\n\n"
        "    if (!capture || !android_relative_mouse_enabled()) return FALSE;\n"
        "    if (!NtUserGetClipCursor( &clip )) return FALSE;\n"
        "    return !EqualRect( &clip, &virtual_screen_rect );\n"
        "}\n\n"
        "/***********************************************************************\n"
        " *           send_event\n"
        " */\n",
    )
    total += n

    src, n = apply_regex(
        src,
        "motion_event relative mode and logging",
        r'jboolean motion_event\( JNIEnv \*env, jobject obj, jint win, jint action, jint x, jint y, jint state, jint vscroll \)\n\{.*?\n\}\n',
        "jboolean motion_event( JNIEnv *env, jobject obj, jint win, jint action, jint x, jint y, jint state, jint vscroll )\n"
        "{\n"
        "    static LONG button_state;\n"
        "    static POINT last_pos;\n"
        "    static HWND last_hwnd;\n"
        "    static BOOL have_last_pos;\n"
        "    union event_data data;\n"
        "    HWND capture;\n"
        "    BOOL relative;\n"
        "    int prev_state;\n"
        "    int delta_x = 0, delta_y = 0;\n"
        "    int mask = action & AMOTION_EVENT_ACTION_MASK;\n\n"
        "    if (!( mask == AMOTION_EVENT_ACTION_DOWN ||\n"
        "           mask == AMOTION_EVENT_ACTION_UP ||\n"
        "           mask == AMOTION_EVENT_ACTION_CANCEL ||\n"
        "           mask == AMOTION_EVENT_ACTION_SCROLL ||\n"
        "           mask == AMOTION_EVENT_ACTION_MOVE ||\n"
        "           mask == AMOTION_EVENT_ACTION_HOVER_MOVE ||\n"
        "           mask == AMOTION_EVENT_ACTION_BUTTON_PRESS ||\n"
        "           mask == AMOTION_EVENT_ACTION_BUTTON_RELEASE ))\n"
        "        return JNI_FALSE;\n\n"
        "    /* make sure a subsequent AMOTION_EVENT_ACTION_UP is not treated as a touch event */\n"
        "    if (mask == AMOTION_EVENT_ACTION_BUTTON_RELEASE) state |= 0x80000000;\n\n"
        "    prev_state = InterlockedExchange( &button_state, state );\n"
        "    capture = get_capture_window();\n"
        "    relative = android_relative_mouse_active( capture );\n\n"
        "    data.type = MOTION_EVENT;\n"
        "    data.motion.hwnd = LongToHandle( win );\n"
        "    data.motion.input.type           = INPUT_MOUSE;\n"
        "    data.motion.input.mi.dx          = x;\n"
        "    data.motion.input.mi.dy          = y;\n"
        "    data.motion.input.mi.mouseData   = 0;\n"
        "    data.motion.input.mi.time        = 0;\n"
        "    data.motion.input.mi.dwExtraInfo = 0;\n"
        "    data.motion.input.mi.dwFlags     = 0;\n\n"
        "    if (relative)\n"
        "    {\n"
        "        if (have_last_pos && last_hwnd == data.motion.hwnd)\n"
        "        {\n"
        "            delta_x = x - last_pos.x;\n"
        "            delta_y = y - last_pos.y;\n"
        "        }\n"
        "        data.motion.input.mi.dx = delta_x;\n"
        "        data.motion.input.mi.dy = delta_y;\n"
        "    }\n"
        "    else\n"
        "    {\n"
        "        data.motion.input.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;\n"
        "    }\n\n"
        "    switch (action & AMOTION_EVENT_ACTION_MASK)\n"
        "    {\n"
        "    case AMOTION_EVENT_ACTION_DOWN:\n"
        "    case AMOTION_EVENT_ACTION_BUTTON_PRESS:\n"
        "        if (!relative) data.motion.input.mi.dwFlags |= MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;\n"
        "        if ((state & ~prev_state) & AMOTION_EVENT_BUTTON_PRIMARY)\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_LEFTDOWN;\n"
        "        if ((state & ~prev_state) & AMOTION_EVENT_BUTTON_SECONDARY)\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_RIGHTDOWN;\n"
        "        if ((state & ~prev_state) & AMOTION_EVENT_BUTTON_TERTIARY)\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_MIDDLEDOWN;\n"
        "        if (!(state & ~prev_state)) /* touch event */\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_LEFTDOWN;\n"
        "        break;\n"
        "    case AMOTION_EVENT_ACTION_UP:\n"
        "    case AMOTION_EVENT_ACTION_CANCEL:\n"
        "    case AMOTION_EVENT_ACTION_BUTTON_RELEASE:\n"
        "        if (!relative) data.motion.input.mi.dwFlags |= MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;\n"
        "        if ((prev_state & ~state) & AMOTION_EVENT_BUTTON_PRIMARY)\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_LEFTUP;\n"
        "        if ((prev_state & ~state) & AMOTION_EVENT_BUTTON_SECONDARY)\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_RIGHTUP;\n"
        "        if ((prev_state & ~state) & AMOTION_EVENT_BUTTON_TERTIARY)\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_MIDDLEUP;\n"
        "        if (!(prev_state & ~state)) /* touch event */\n"
        "            data.motion.input.mi.dwFlags |= MOUSEEVENTF_LEFTUP;\n"
        "        break;\n"
        "    case AMOTION_EVENT_ACTION_SCROLL:\n"
        "        if (!relative) data.motion.input.mi.dwFlags |= MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE;\n"
        "        data.motion.input.mi.dwFlags |= MOUSEEVENTF_WHEEL;\n"
        "        data.motion.input.mi.mouseData = vscroll < 0 ? -WHEEL_DELTA : WHEEL_DELTA;\n"
        "        break;\n"
        "    case AMOTION_EVENT_ACTION_MOVE:\n"
        "    case AMOTION_EVENT_ACTION_HOVER_MOVE:\n"
        "        data.motion.input.mi.dwFlags |= MOUSEEVENTF_MOVE;\n"
        "        if (!relative) data.motion.input.mi.dwFlags |= MOUSEEVENTF_ABSOLUTE;\n"
        "        break;\n"
        "    default:\n"
        "        return JNI_FALSE;\n"
        "    }\n\n"
        "    if (android_input_debug_enabled())\n"
        "    {\n"
        '        p__android_log_print( ANDROID_LOG_INFO, "wine",\n'
        '                              "INPUTDBG android.motion mode=%s hwnd=%p capture=%p action=%d pos=%d,%d delta=%d,%d flags=%#x buttons=%#x",\n'
        "                              relative ? \"relative\" : \"absolute\", data.motion.hwnd, capture, mask, x, y,\n"
        "                              delta_x, delta_y, (unsigned int)data.motion.input.mi.dwFlags, (unsigned int)state );\n"
        "    }\n\n"
        "    last_pos.x = x;\n"
        "    last_pos.y = y;\n"
        "    last_hwnd = data.motion.hwnd;\n"
        "    have_last_pos = TRUE;\n"
        "    send_event( &data );\n"
        "    return JNI_TRUE;\n"
        "}\n",
    )
    total += n

    with open(window_c, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    print(f"\nDone. Applied {total} fix(es) to wineandroid window.c")


if __name__ == "__main__":
    main()
