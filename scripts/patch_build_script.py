#!/usr/bin/env python3
"""
Patch build-step-arm64ec.sh so required Android/GameNative patches either apply,
are already present, or fail the build.

For drift-prone patches we try, in order:
1) reverse-check for already-applied
2) git apply with loose whitespace/context
3) git apply 3-way
4) GNU patch (fuzzy line-offset application)
Then fail if none work.

test-bylaws patches keep a marker-based already-applied fast path because
reverse-checks can fail under heavy drift even when the content is present.
"""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'build-scripts/build-step-arm64ec.sh'

with open(path) as f:
    txt = f.read()

txt = txt.replace(
    'git apply ./android/patches/$patch',
    # For test-bylaws patches: use grep-based marker check as primary already-applied
    # detection. git apply -R --check fails when context has drifted even if the
    # patch content is present, causing false "critical patch failed" errors.
    # The markers here are unique symbols introduced by each patch.
    'if [[ "$patch" == test-bylaws/* ]]; then '
    '_patch_marker=""; '
    'case "$patch" in '
    '  test-bylaws/dlls_ntdll_signal_arm64ec_c.patch) _patch_marker="ARM64EC_NT_XCONTEXT" _patch_file="dlls/ntdll/signal_arm64ec.c" ;; '
    '  test-bylaws/dlls_ntdll_signal_arm64_c.patch)   _patch_marker="RtlWow64SuspendThread" _patch_file="dlls/ntdll/signal_arm64.c" ;; '
    '  test-bylaws/dlls_ntdll_signal_x86_64_c.patch)  _patch_marker="RtlWow64SuspendThread" _patch_file="dlls/ntdll/signal_x86_64.c" ;; '
    '  test-bylaws/dlls_ntdll_ntdll_spec.patch)        _patch_marker="RtlWow64SuspendThread" _patch_file="dlls/ntdll/ntdll.spec" ;; '
    '  test-bylaws/dlls_ntdll_ntdll_misc_h.patch)      _patch_marker="pWow64SuspendLocalThread" _patch_file="dlls/ntdll/ntdll_misc.h" ;; '
    '  test-bylaws/tools_makedep_c.patch)              _patch_marker="arch_install_dirs[arch] = strmake( \\"$(libdir)/wine/%s-windows\\", archs.str[arch] );" _patch_file="tools/makedep.c" ;; '
    '  test-bylaws/server_thread_h.patch)              _patch_marker="bypass_proc_suspend" _patch_file="server/thread.h" ;; '
    '  test-bylaws/server_thread_c.patch)              _patch_marker="bypass_proc_suspend" _patch_file="server/thread.c" ;; '
    '  test-bylaws/server_process_c.patch)             _patch_marker="bypass_proc_suspend" _patch_file="server/process.c" ;; '
    '  test-bylaws/dlls_ntdll_unix_thread_c.patch)     _patch_marker="BYPASS_PROCESS_FREEZE" _patch_file="dlls/ntdll/unix/thread.c" ;; '
    '  test-bylaws/include_winternl_h.patch)           _patch_marker="ProcessFexHardwareTso" _patch_file="include/winternl.h" ;; '
    'esac; '
    'if [[ -n "$_patch_marker" ]] && grep -qF "$_patch_marker" "$_patch_file" 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'elif git apply --ignore-whitespace -C1 --check ./android/patches/$patch 2>/dev/null'
    ' && git apply --ignore-whitespace -C1 ./android/patches/$patch; then '
    '  echo "Applied: $patch"; '
    'elif git apply --3way --ignore-space-change ./android/patches/$patch 2>/dev/null; then '
    '  echo "Applied (3way): $patch"; '
    'elif patch -p1 --forward --batch --ignore-whitespace -i ./android/patches/$patch 2>/dev/null; then '
    '  echo "Applied (patch): $patch"; '
    'elif git apply --ignore-whitespace -C1 -R --check ./android/patches/$patch 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'else '
    '  echo "ERROR: critical patch failed: $patch"; exit 1; '
    'fi; '
    'else '
    'if [[ "$patch" == "dlls_winex11_drv_x11drv_h.patch" ]] && grep -qF "XATOM__NET_WM_HWND" "dlls/winex11.drv/x11drv.h" 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'elif [[ "$patch" == "dlls_winex11_drv_x11drv_main_c.patch" ]] && grep -qF "\"_NET_WM_HWND\"" "dlls/winex11.drv/x11drv_main.c" 2>/dev/null && grep -qF "#ifdef HAVE_X11_EXTENSIONS_XINPUT2_H" "dlls/winex11.drv/x11drv_main.c" 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'elif [[ "$patch" == "dlls_winex11_drv_opengl_c.patch" ]] && grep -qF "int wine_x11forceglx = 0;" "dlls/winex11.drv/opengl.c" 2>/dev/null && grep -qF "atoi(getenv(\"WINE_X11FORCEGLX\"))" "dlls/winex11.drv/opengl.c" 2>/dev/null && grep -qF "|| wine_x11forceglx)" "dlls/winex11.drv/opengl.c" 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'elif [[ "$patch" == "programs_winemenubuilder_winemenubuilder_c.patch" ]] && grep -qF "icons\\\\hicolor" "programs/winemenubuilder/winemenubuilder.c" 2>/dev/null && grep -qF "_wgetenv( L\"WINECONFIGDIR\" )" "programs/winemenubuilder/winemenubuilder.c" 2>/dev/null && grep -qF "fprintf(file, \"wine %s\", escape(path));" "programs/winemenubuilder/winemenubuilder.c" 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'elif git apply --ignore-whitespace -C1 -R --check ./android/patches/$patch 2>/dev/null; then '
    '  echo "ALREADY APPLIED (skipped): $patch"; '
    'elif git apply --ignore-whitespace -C1 --check ./android/patches/$patch 2>/dev/null'
    ' && git apply --ignore-whitespace -C1 ./android/patches/$patch; then '
    '  echo "Applied: $patch"; '
    'elif git apply --3way --ignore-space-change ./android/patches/$patch 2>/dev/null; then '
    '  echo "Applied (3way): $patch"; '
    'elif patch -p1 --forward --batch --ignore-whitespace -i ./android/patches/$patch 2>/dev/null; then '
    '  echo "Applied (patch): $patch"; '
    'else '
    '  echo "ERROR: required patch failed: $patch"; exit 1; '
    'fi; '
    'fi'
)

txt = txt.replace(
    '    done\n  fi',
    '    done\n'
    '    if [ -x ./tools/make_requests ]; then ./tools/make_requests; fi\n'
    '    if [ -x ./config.status ]; then ./config.status; fi\n'
    '  fi'
)

with open(path, 'w') as f:
    f.write(txt)

print(f"Patched {path}")
