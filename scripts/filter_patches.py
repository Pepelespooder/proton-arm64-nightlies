#!/usr/bin/env python3
"""
Removes patches from build-step-arm64ec.sh's PATCHES array that are already
present in the source tree, to avoid double-apply errors when building against
bleeding-edge (which has many of GameNative's patches already merged).

Usage: filter_patches.py <build-script-path> <wine-source-path>
"""
import os
import re
import sys


# Maps patch filename -> (file to check, marker spec added by the patch).
# Marker specs can be:
# - a string: skip if the string is present
# - a list/tuple/set of strings: skip if all markers are present
# GE-style upfront exclusions: these signal patch pieces are already present in
# the Valve bleeding-edge base we are building against, and reapplying them creates
# duplicate definitions before the BYLAWS helper even runs.
FORCE_SKIP = {
    "test-bylaws/dlls_ntdll_signal_arm64_c.patch",
    "test-bylaws/dlls_ntdll_signal_arm64ec_c.patch",
    "test-bylaws/dlls_ntdll_signal_x86_64_c.patch",
    "dlls_ntdll_unix_fsync_c.patch",
    "server_fsync_c.patch",
}

ALREADY_APPLIED = {
    # Handled by fix_window_c.py / fix_mouse_c.py - skip these patches so
    # git apply never sees their drift-prone hunks against bleeding-edge.
    "dlls_winex11_drv_window_c.patch":      ("dlls/winex11.drv/window.c",    "steam_proton"),
    "dlls_winex11_drv_mouse_c.patch":       ("dlls/winex11.drv/mouse.c",     ["clip_center", "needs_relative_motion", "get_send_mouse_flags"]),
    "dlls_wineandroid_drv_window_c.patch":  ("dlls/wineandroid.drv/window.c", ["WINE_ANDROID_RELATIVE_MOUSE", "android_relative_mouse_active", "INPUTDBG android.motion"]),

    # These are all merged into ValveSoftware/wine bleeding-edge already.
    "dlls_ntdll_loader_c.patch":            ("dlls/ntdll/loader.c",          "libarm64ecfex.dll"),
    "dlls_ntdll_unix_loader_c.patch":       ("dlls/ntdll/unix/loader.c",     "__aarch64__"),
    "dlls_wow64_syscall_c.patch":           ("dlls/wow64/syscall.c",         "libwow64fex.dll"),
    "loader_wine_inf_in.patch":             ("loader/wine.inf.in",           "libarm64ecfex.dll"),
    "programs_wineboot_wineboot_c.patch":   ("programs/wineboot/wineboot.c", "initialize_xstate_features"),
    "dlls_ntdll_unix_process_c.patch":      ("dlls/ntdll/unix/process.c",    "ProcessFexHardwareTso"),

    # fsync is explicitly disabled on Android by fix_fsync.py, so these
    # drift-prone patches must not be required for the build to proceed.
    "dlls_ntdll_unix_fsync_c.patch":        ("dlls/ntdll/unix/fsync.c",      "#if defined(__linux__) && !defined(__ANDROID__)"),
    "server_fsync_c.patch":                 ("server/fsync.c",                "#if defined(__linux__) && !defined(__ANDROID__)"),

    # test-bylaws patches
    "test-bylaws/dlls_ntdll_unwind_h.patch":         ("dlls/ntdll/unwind.h",         ["CONTEXT_ARM64_FEX_YMMSTATE", "CONTEXT_AMD64_XSTATE"]),
    "test-bylaws/include_winnt_h.patch":             ("include/winnt.h",              "CONTEXT_ARM64_FEX_YMMSTATE"),
    "test-bylaws/dlls_ntdll_signal_arm64_c.patch":   ("dlls/ntdll/signal_arm64.c",    ["RtlWow64SuspendThread", "suspend_remote_breakin"]),
    "test-bylaws/dlls_ntdll_signal_arm64ec_c.patch": ("dlls/ntdll/signal_arm64ec.c",  "RtlWow64SuspendThread"),
    "test-bylaws/dlls_ntdll_signal_x86_64_c.patch":  ("dlls/ntdll/signal_x86_64.c",   "RtlWow64SuspendThread"),
    "test-bylaws/dlls_ntdll_ntdll_spec.patch":       ("dlls/ntdll/ntdll.spec",        "RtlWow64SuspendThread"),
    "test-bylaws/dlls_ntdll_ntdll_misc_h.patch":     ("dlls/ntdll/ntdll_misc.h",      "pWow64SuspendLocalThread"),
    "test-bylaws/dlls_wow64_wow64_spec.patch":       ("dlls/wow64/wow64.spec",        "Wow64SuspendLocalThread"),
    "test-bylaws/dlls_wow64_virtual_c.patch":        ("dlls/wow64/virtual.c",         "old_prot_ptr"),
    "test-bylaws/server_process_c.patch":            ("server/process.c",             "bypass_proc_suspend"),
    "test-bylaws/dlls_ntdll_unix_process_c.patch":   ("dlls/ntdll/unix/process.c",    "ProcessFexHardwareTso"),
    "test-bylaws/dlls_wow64_process_c.patch":        ("dlls/wow64/process.c",         "wow64_NtSuspendThread"),
    "test-bylaws/server_thread_h.patch":             ("server/thread.h",              "bypass_proc_suspend"),
    "test-bylaws/server_thread_c.patch":             ("server/thread.c",              "bypass_proc_suspend"),
    "test-bylaws/dlls_ntdll_unix_thread_c.patch":    ("dlls/ntdll/unix/thread.c",     "BYPASS_PROCESS_FREEZE"),
    "test-bylaws/include_winternl_h.patch":          ("include/winternl.h",           "ProcessFexHardwareTso"),
    "test-bylaws/tools_makedep_c.patch":             ("tools/makedep.c",              ["arch_install_dirs[arch] = \"$(libdir)/wine/aarch64-windows/\";", "output_symlink_rule("]),
}


def is_already_applied(wine_src, rel_file, markers):
    path = os.path.join(wine_src, rel_file)
    if not os.path.exists(path):
        return False

    with open(path, errors='replace') as f:
        text = f.read()

    if isinstance(markers, (list, tuple, set)):
        return all(marker in text for marker in markers)
    return markers in text


def main():
    if len(sys.argv) < 3:
        print("Usage: filter_patches.py <build-script> <wine-source-dir>")
        sys.exit(1)

    script_path = sys.argv[1]
    wine_src = sys.argv[2]

    with open(script_path) as f:
        content = f.read()

    skipped = []
    for patch_name, (rel_file, markers) in ALREADY_APPLIED.items():
        if patch_name in FORCE_SKIP:
            pattern = r'(\s*)"' + re.escape(patch_name) + r'"'
            replacement = r'\1# (GE-style pre-exclude) # "' + patch_name + '"'
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                skipped.append(patch_name)
                print(f"SKIP (GE-style pre-exclude): {patch_name}")
            else:
                print(f"NOT FOUND IN SCRIPT (no change): {patch_name}")
            continue
        if is_already_applied(wine_src, rel_file, markers):
            pattern = r'(\s*)"' + re.escape(patch_name) + r'"'
            replacement = r'\1# (already in bleeding-edge) # "' + patch_name + '"'
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                content = new_content
                skipped.append(patch_name)
                print(f"SKIP (already applied): {patch_name}")
            else:
                print(f"NOT FOUND IN SCRIPT (no change): {patch_name}")
        else:
            print(f"APPLY: {patch_name}")

    with open(script_path, 'w') as f:
        f.write(content)

    print(f"\nDone. Skipped {len(skipped)} already-applied patches.")


if __name__ == "__main__":
    main()


