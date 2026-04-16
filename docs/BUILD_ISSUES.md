# Known Build Issues and Solutions

## Issue 1: Wrong artifact format used for the target app

**Symptom:** Import fails, or the consumer rejects the package.

**Cause:** This repo produces two different package formats:

- `proton-*.wcp` is Zstandard-compressed and targets GameNative Proton import
- `proton-wine-*.wcp.xz` is XZ-compressed and targets Ludashi/CMOD-style import

**Fix:** Use the artifact that matches the target app.

## Issue 2: Stock GameNative does not recognize non-numeric Proton versions

**Symptom:** The build imports, but the app does not classify it correctly as ARM64EC Proton.

**Cause:** Stock GameNative's existing parser only accepts numeric Proton version identifiers.

**Fix:** Keep the internal profile version numeric. The workflow currently uses:

```text
11
```

while still keeping the external release naming on `bleeding-edge`.

## Issue 3: Runtime built against `/opt/wine` instead of the imported Proton path

**Symptom:** Wine starts and then dies during early startup with errors like `could not load kernel32.dll`.

**Cause:** The runtime was built against `/opt/wine`, but the package was imported under `/opt/proton-*`.

**Fix:** Keep the baked install path aligned with the internal profile version. The current workflow bakes:

```text
/data/data/com.winlator.cmod/files/imagefs/opt/proton-11
```

## Issue 4: Drift in GameNative patch application

**Symptom:** Build breaks during patching or later during ARM64EC linking.

**Cause:** The GameNative patch stack drifts against Valve `bleeding-edge`.

**Fix:** This repo uses local fix scripts to patch around drift. If bleeding-edge moves again, update those scripts instead of assuming the upstream patch series still applies unchanged.

## Issue 5: Donor overlay confusion

**Symptom:** It is unclear whether a working build depends on donor files.

**Cause:** Earlier workflow iterations had an optional donor/kernel compatibility overlay.

**Fix:** The current workflow no longer includes any donor or kernel compatibility overlay. If a build works now, it is working on its own compiled runtime.
