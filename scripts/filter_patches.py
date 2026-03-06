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


# Maps patch filename -> (file to check, unique string added by the patch).
# If the unique string is already in the file, the patch is skipped.
ALREADY_APPLIED = {
    # These are all merged into ValveSoftware/wine bleeding-edge already.
    "dlls_ntdll_loader_c.patch":            ("dlls/ntdll/loader.c",          "libarm64ecfex.dll"),
    "dlls_ntdll_unix_loader_c.patch":       ("dlls/ntdll/unix/loader.c",     "__aarch64__"),
    "dlls_wow64_syscall_c.patch":           ("dlls/wow64/syscall.c",          "libwow64fex.dll"),
    "loader_wine_inf_in.patch":             ("loader/wine.inf.in",            "libarm64ecfex.dll"),
    "programs_wineboot_wineboot_c.patch":   ("programs/wineboot/wineboot.c",  "initialize_xstate_features"),
    "dlls_wdscore_wdscore_spec.patch":      ("dlls/wdscore/wdscore.spec",     "WdsGetPointer"),
    "dlls_ntdll_unix_process_c.patch":      ("dlls/ntdll/unix/process.c",     "ProcessFexHardwareTso"),
    # test-bylaws patches
    "test-bylaws/dlls_ntdll_unwind_h.patch":         ("dlls/ntdll/unwind.h",          "CONTEXT_ARM64_FEX_YMMSTATE"),
    "test-bylaws/include_winnt_h.patch":             ("include/winnt.h",               "XSTATE_AVX512"),
    "test-bylaws/dlls_ntdll_signal_arm64_c.patch":   ("dlls/ntdll/signal_arm64.c",    "SuspendLocalThread"),
    "test-bylaws/dlls_ntdll_signal_arm64ec_c.patch": ("dlls/ntdll/signal_arm64ec.c",  "ARM64EC_NT_XCONTEXT"),
    "test-bylaws/dlls_ntdll_signal_x86_64_c.patch":  ("dlls/ntdll/signal_x86_64.c",  "RtlWow64SuspendThread"),
    "test-bylaws/dlls_ntdll_ntdll_spec.patch":       ("dlls/ntdll/ntdll.spec",        "RtlWow64SuspendThread"),
    "test-bylaws/dlls_ntdll_ntdll_misc_h.patch":     ("dlls/ntdll/ntdll_misc.h",      "pWow64SuspendLocalThread"),
    "test-bylaws/dlls_wow64_wow64_spec.patch":        ("dlls/wow64/wow64.spec",        "Wow64SuspendLocalThread"),
    "test-bylaws/dlls_wow64_virtual_c.patch":         ("dlls/wow64/virtual.c",         "old_prot_ptr"),
    "test-bylaws/server_process_c.patch":             ("server/process.c",             "bypass_proc_suspend"),
    "test-bylaws/dlls_ntdll_unix_process_c.patch":    ("dlls/ntdll/unix/process.c",    "ProcessFexHardwareTso"),
    "test-bylaws/server_thread_h.patch":              ("server/thread.h",              "bypass_proc_suspend"),
    "test-bylaws/server_thread_c.patch":              ("server/thread.c",              "bypass_proc_suspend"),
    "test-bylaws/dlls_ntdll_unix_thread_c.patch":     ("dlls/ntdll/unix/thread.c",     "BYPASS_PROCESS_FREEZE"),
    "test-bylaws/include_winternl_h.patch":           ("include/winternl.h",           "ProcessFexHardwareTso"),
}


def is_already_applied(wine_src, rel_file, search_str):
    path = os.path.join(wine_src, rel_file)
    if not os.path.exists(path):
        return False
    with open(path, errors='replace') as f:
        return search_str in f.read()


def main():
    if len(sys.argv) < 3:
        print("Usage: filter_patches.py <build-script> <wine-source-dir>")
        sys.exit(1)

    script_path = sys.argv[1]
    wine_src = sys.argv[2]

    with open(script_path) as f:
        content = f.read()

    skipped = []
    for patch_name, (rel_file, search_str) in ALREADY_APPLIED.items():
        if is_already_applied(wine_src, rel_file, search_str):
            # Comment out the patch entry in the PATCHES array
            # Matches: optional whitespace + quoted patch name + optional whitespace
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
