#!/usr/bin/env python3
"""
Apply the GameNative/Winlator winemenubuilder.c changes directly when the
original patch drifts against newer Proton/Wine sources.
"""
import os
import sys


def apply(src, description, old, new):
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
        print("Usage: fix_winemenubuilder_c.py <wine-source-dir>")
        return 1

    path = os.path.join(sys.argv[1], "programs", "winemenubuilder", "winemenubuilder.c")
    if not os.path.exists(path):
        print(f"ERROR: missing file {path}")
        return 2

    with open(path, encoding="utf-8", errors="replace") as f:
        src = f.read()

    total = 0

    src, n = apply(
        src,
        "icon directory under xdg_data_dir",
        '    *nativeIdentifier = compute_native_identifier(exeIndex, icoPathW, destFilename);\n'
        '    iconsDir = heap_wprintf(L"%s", L"c:\\\\proton_shortcuts\\\\icons");\n'
        '    create_directories(iconsDir);\n',
        '    *nativeIdentifier = compute_native_identifier(exeIndex, icoPathW, destFilename);\n'
        '    iconsDir = heap_wprintf(L"%s\\\\icons\\\\hicolor", xdg_data_dir);\n',
    )
    total += n

    src, n = apply(
        src,
        "desktop entry location and WINEPREFIX env",
        '    char *workdir_unix;\n'
        '    int needs_chmod = FALSE;\n'
        '    const WCHAR *name;\n'
        '    WCHAR *shortcuts_dir;\n'
        '\n'
        '    WINE_TRACE("(%s,%s,%s,%s,%s,%s,%s,%s,%s)\\n", wine_dbgstr_w(link), wine_dbgstr_w(location),\n'
        '               wine_dbgstr_w(linkname), wine_dbgstr_w(path), wine_dbgstr_w(args),\n'
        '               wine_dbgstr_w(descr), wine_dbgstr_w(workdir), wine_dbgstr_w(icon),\n'
        '               wine_dbgstr_w(wmclass));\n'
        '\n'
        '    name = PathFindFileNameW( linkname );\n'
        '\n'
        '    shortcuts_dir = heap_wprintf(L"%s", L"c:\\\\proton_shortcuts");\n'
        '    create_directories(shortcuts_dir);\n'
        '    location = heap_wprintf(L"%s\\\\%s.desktop", shortcuts_dir, name);\n'
        '    heap_free(shortcuts_dir);\n'
        '    needs_chmod = TRUE;\n'
        '\n'
        '    file = _wfopen( location, L"wb" );\n'
        '    if (file == NULL)\n'
        '        return FALSE;\n'
        '\n'
        '    fprintf(file, "[Desktop Entry]\\n");\n'
        '    fprintf(file, "Name=%s\\n", wchars_to_utf8_chars(name));\n'
        '    fprintf(file, "Exec=" );\n'
        '\n',
        '    char *workdir_unix;\n'
        '    int needs_chmod = FALSE;\n'
        '    const WCHAR *name;\n'
        '    const WCHAR *prefix = _wgetenv( L"WINECONFIGDIR" );\n'
        '\n'
        '    WINE_TRACE("(%s,%s,%s,%s,%s,%s,%s,%s,%s)\\n", wine_dbgstr_w(link), wine_dbgstr_w(location),\n'
        '               wine_dbgstr_w(linkname), wine_dbgstr_w(path), wine_dbgstr_w(args),\n'
        '               wine_dbgstr_w(descr), wine_dbgstr_w(workdir), wine_dbgstr_w(icon),\n'
        '               wine_dbgstr_w(wmclass));\n'
        '\n'
        '    name = PathFindFileNameW( linkname );\n'
        '    if (!location)\n'
        '    {\n'
        '        location = heap_wprintf(L"%s\\\\%s.desktop", xdg_desktop_dir, name);\n'
        '        needs_chmod = TRUE;\n'
        '    }\n'
        '\n'
        '    file = _wfopen( location, L"wb" );\n'
        '    if (file == NULL)\n'
        '        return FALSE;\n'
        '\n'
        '    fprintf(file, "[Desktop Entry]\\n");\n'
        '    fprintf(file, "Name=%s\\n", wchars_to_utf8_chars(name));\n'
        '    fprintf(file, "Exec=" );\n'
        '    if (prefix)\n'
        '    {\n'
        '        char *path = wine_get_unix_file_name( prefix );\n'
        '        fprintf(file, "env WINEPREFIX=\\"%s\\" ", path);\n'
        '        heap_free( path );\n'
        '    }\n'
        '\n',
    )
    total += n

    src, n = apply(
        src,
        "desktop entry exec uses wine prefix launcher",
        '    fprintf(file, "\\"%s\\"", escape(path));\n'
        '    if (args) fprintf(file, " \\"%s\\"", escape(args) );\n',
        '    fprintf(file, "wine %s", escape(path));\n'
        '    if (args) fprintf(file, " %s", escape(args) );\n',
    )
    total += n

    with open(path, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"\\nDone. Applied {total} fix(es) to winemenubuilder.c")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
