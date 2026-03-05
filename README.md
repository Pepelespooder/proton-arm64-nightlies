# Proton ARM64 Nightlies for Winlator

Nightly builds of Proton for Android ARM64, packaged as `.wcp` files ready to drop into Winlator Cmod. Builds run automatically every night pulling the latest commits straight from Valve's bleeding-edge Wine branch, with GameNative's Android and ARM64EC patches layered on top.

## Getting a build

1. Head to [Releases](../../releases) and grab the latest `.wcp` file
2. Copy it to your Android device
3. Open Winlator → Settings → Wine Version → Import
4. Pick the file, then select it in your container settings

That's it. If you want more detail on installation, [USER_GUIDE.md](docs/USER_GUIDE.md) has you covered.

## What's inside

Each build includes:

- Wine for ARM64 Android (built with NDK r27d, targeting Android 9+)
- ARM64EC Windows PE DLLs — for running ARM64 Windows apps natively
- ARM64 and 32-bit (WoW64) PE DLLs
- A default Wine prefix (`prefixPack.txz`) so things work out of the box

There are two package formats per build:

| File | For |
|------|-----|
| `.wcp` | Standard Winlator / GameNative |
| `.wcp.xz` | Winlator Cmod / Ludashi |

## Where the source comes from

The base Wine source is **Valve's `bleeding-edge` branch** — the same branch that Proton bleeding-edge tracks internally. On top of that, Android support and ARM64EC patches come from [GameNative/proton-wine](https://github.com/GameNative/proton-wine). Every nightly picks up whatever Valve pushed that day automatically.

## Build status

Builds kick off at 2 AM UTC daily. You can check whether the latest run succeeded in the [Actions tab](../../actions). The [latest.json](latest.json) file always reflects the most recent successful build.

## Docs

- [WCP_STRUCTURE.md](docs/WCP_STRUCTURE.md) — how the `.wcp` format works
- [BUILD_REQUIREMENTS.md](docs/BUILD_REQUIREMENTS.md) — what you need to build locally
- [BUILD_ISSUES.md](docs/BUILD_ISSUES.md) — known issues and fixes
- [USER_GUIDE.md](docs/USER_GUIDE.md) — installation walkthrough
- [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) — how to contribute or fork

## License

The scripts in this repo are MIT licensed. Wine itself is LGPL. See [LICENSE](LICENSE).
