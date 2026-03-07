#!/usr/bin/env python3
"""
Comment out only patches that are either:
- intentionally handled by local fix scripts, or
- already merged into Valve bleeding-edge with stable identifying markers.

Everything else stays in build-step-arm64ec.sh so patch_build_script.py can
attempt a real apply/reverse-check/3way merge instead of being skipped on weak
heuristics.

Usage: filter_patches.py <build-script-path> <wine-source-path>
"""
import os
import re
import sys


# Only use this list for patches we are confident are already present upstream
# or replaced locally. Anything drift-prone but still required should not be
# filtered here.
+FILTERED_PATCHES = {
+    "dlls_winex11_drv_window_c.patch": ("dlls/winex11.drv/window.c", ["steam_proton"], "handled by fix_window_c.py"),
+    "dlls_ntdll_loader_c.patch": ("dlls/ntdll/loader.c", ["libarm64ecfex.dll"], "already in bleeding-edge"),
+    "dlls_ntdll_unix_loader_c.patch": ("dlls/ntdll/unix/loader.c", ["__aarch64__"], "already in bleeding-edge"),
+    "dlls_wow64_syscall_c.patch": ("dlls/wow64/syscall.c", ["libwow64fex.dll"], "already in bleeding-edge"),
+    "loader_wine_inf_in.patch": ("loader/wine.inf.in", ["libarm64ecfex.dll"], "already in bleeding-edge"),
+    "programs_wineboot_wineboot_c.patch": ("programs/wineboot/wineboot.c", ["initialize_xstate_features"], "handled by fix_wineboot_c.py / already in bleeding-edge"),
+    "dlls_ntdll_unix_process_c.patch": ("dlls/ntdll/unix/process.c", ["ProcessFexHardwareTso"], "already in bleeding-edge"),
+}
-
-
-# Only patches replaced by local fix scripts should be filtered here.
-# Anything else must remain in the PATCHES array so patch_build_script.py can
-# try to apply it properly even when upstream has drifted.
-HANDLED_LOCALLY = {
-    "dlls_winex11_drv_window_c.patch": "handled by fix_window_c.py",
-}
+
+
+def has_any_marker(wine_src, rel_path, markers):
+    full = os.path.join(wine_src, rel_path)
+    if not os.path.exists(full):
+        return False
+    with open(full, errors="replace") as f:
+        text = f.read()
+    return any(marker in text for marker in markers)
 
 
 def main():
     if len(sys.argv) < 3:
         print("Usage: filter_patches.py <build-script> <wine-source-dir>")
         sys.exit(1)
 
     script_path = sys.argv[1]
+    wine_src = sys.argv[2]
 
     with open(script_path) as f:
         content = f.read()
 
     skipped = []
-    for patch_name, reason in HANDLED_LOCALLY.items():
+    for patch_name, (rel_path, markers, reason) in FILTERED_PATCHES.items():
+        if not has_any_marker(wine_src, rel_path, markers):
+            print(f"APPLY: {patch_name}")
+            continue
         pattern = r'(\s*)"' + re.escape(patch_name) + r'"'
         replacement = r'\1# (' + reason + r') # "' + patch_name + '"'
         new_content = re.sub(pattern, replacement, content)
         if new_content != content:
             content = new_content
             skipped.append(patch_name)
             print(f"SKIP ({reason}): {patch_name}")
         else:
             print(f"NOT FOUND IN SCRIPT (no change): {patch_name}")
 
     with open(script_path, 'w') as f:
         f.write(content)
 
-    print(f"\nDone. Skipped {len(skipped)} locally handled patch(es).")
+    print(f"\nDone. Skipped {len(skipped)} upstream/local-handled patch(es).")
 
 
 if __name__ == "__main__":
     main()
