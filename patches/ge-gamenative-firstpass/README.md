# GE GameNative First Pass

Filtered non-Wayland GE patch pack for GameNative / Winlator ARM64 experiments.

Source:
- `C:\Users\Makin\Desktop\Proton build\proton-ge-arm64\patches\ge-wine-only-wrapper`

Intent:
- keep the first GE import small
- avoid Wayland-specific work entirely
- focus on generic compatibility/stability patches first

## Included patches

1. `proton/fix-a-crash-in-ID2D1DeviceContext-if-no-target-is-set.patch`
2. `proton/0001-win32u-add-env-switch-to-disable-wm-decorations.patch`
3. `proton/83-nv_low_latency_wine.patch`
4. `wine-hotfixes/pending/unity_crash_hotfix.patch`
5. `wine-hotfixes/pending/registry_RRF_RT_REG_SZ-RRF_RT_REG_EXPAND_SZ.patch`
6. `wine-hotfixes/pending/ntdll_add_wine_disable_sfn.patch`
7. `wine-hotfixes/pending/NCryptDecrypt_implementation.patch`
8. `wine-hotfixes/pending/webview2.patch`
9. `shell32/shell32_shlfileop_init_path_components.patch`
10. `wine-hotfixes/staging/cryptext-CryptExtOpenCER/0001.patch`
11. `wine-hotfixes/staging/wineboot-ProxySettings/0001.patch`
12. `proton/0001-fshack-Implement-AMD-FSR-upscaler-for-fullscreen-hac.patch`
13. `explorer/explorer_startmenu_shutdown_latch.patch`
## Suggested apply order

Apply in this order:

1. `fix-a-crash-in-ID2D1DeviceContext-if-no-target-is-set.patch`
2. `0001-win32u-add-env-switch-to-disable-wm-decorations.patch`
3. `83-nv_low_latency_wine.patch`
4. pending hotfixes
5. staging hotfixes
6. `0001-fshack-Implement-AMD-FSR-upscaler-for-fullscreen-hac.patch` last

## Explicit exclusions

- entire `wine-hotfixes/wine-wayland/` tree
- `proton/add-envvar-to-gate-media-converter.patch`
- `proton/build_failure_prevention-add-nls.patch`
- all per-game patches

## Notes

- `0001-fshack-Implement-AMD-FSR-upscaler-for-fullscreen-hac.patch` is intentionally included but should be treated as optional until the smaller set builds and runs cleanly.
- If build drift becomes too high, split this pack again into `core` and `optional`.

