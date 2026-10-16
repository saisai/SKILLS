---
name: inno-setup
description: >-
  Adds a Windows Inno Setup 6 script named {slug}-setup.iss under
  scripts/package, using the repo's packaging layout (ISCC, dist staging,
  PowerShell install and uninstall hooks, PATH and upgrade handling). Use
  when the user asks to add an Inno Setup script, a {name}-setup.iss file,
  a Windows installer, or ISCC packaging, or points at scripts/ for the
  installer.
---

# Inno Setup script

Add one Inno Setup 6 script: `scripts/package/{slug}-setup.iss`.

`{slug}` is the lowercase product id (letters, digits, hyphens). The user writes it as `{name}-setup.iss`. Example: slug `ticketsystem` → `scripts/package/ticketsystem-setup.iss`.

## Before writing

Read the packaging that already exists. Start in `scripts/`, then `scripts/package/` if present:

- `*-setup.iss`
- `package.ps1` (how `ISCC.exe` is invoked and which `/D` defines it passes)
- `scripts/*.ps1` and `scripts/*.cmd` (install, preinstall, uninstall, health check)
- `config/`
- `VERSION`
- staged folder name under `dist/`
- launcher exe, icon (`.ico`), migrations, bundled runtimes (`pgsql`, `redis`, `nginx`)

Use names, paths, and binaries from that tree. If `scripts/package/{slug}-setup.iss` already exists, update it. Do not add a second installer script unless the user asked for another product.

If this repo has no `scripts/package/` yet, create the directory and the `.iss` only. Do not invent PowerShell service installers, nginx configs, or a packager unless the user asked for those too.

## Fill the script

Start from [template.iss](template.iss). Replace every `__TOKEN__`. Delete every block whose comment says OPTIONAL when this repo has no matching file or feature.

Paths inside the `.iss` are relative to the script file. For `scripts/package/{slug}-setup.iss`:

- repo root: `..\..`
- dist: `..\..\dist`
- helper scripts copied into the installer's temp dir: `scripts` (the `scripts/package/scripts` folder)

Version is overridable. Keep:

```text
#ifndef MyAppVersion
#define MyAppVersion "0.0.1"
#endif
```

Read the default from `VERSION` when that file exists. The packager passes the real value as `ISCC /DMyAppVersion=$Version`.

Generate a new `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` AppId for a new product. Never reuse an AppId from another product or from the template.

`OutputBaseFilename` is `{ProductToken}-Setup-x64-{#MyAppVersion}`. `OutputDir` is the repo `dist` folder. The staged payload is `{#DistDir}\{DistFolder}\*` copied to `{app}`.

## Hooks the script may call

Reference a hook only when that file exists under `scripts/package/scripts/` (or you are adding it in the same task):

| File | When the installer runs it |
|------|----------------------------|
| `common.ps1`, `preinstall.ps1` | `PrepareToInstall`, extracted with `dontcopy`. Exit code `2` means a required port is taken. |
| `install.ps1` | `ssPostInstall`, args `-Root "{app}" -Version "{version}"` and `-Seed` when that task is selected. Failures are lines containing `[ERROR]` in `{app}\logs\install.log`. |
| `install.cmd` | Shown in the failure dialog so the user can retry. |
| `uninstall.cmd`, `remove-data.cmd` | `[UninstallRun]`, uninstall first, then data removal. |
| `health-check.cmd` | Start-menu shortcut. |

Seed data is a task only when install accepts `-Seed`. Offer it when `{app}\config\install-state.json` does not exist yet.

PATH editing belongs in `[Code]` (`NeedsAddToPath`, `AddToPath`, `CurUninstallStepChanged`), not a raw registry append, and only when the script has an "add bin to PATH" task.

## Packager

If `scripts/package/package.ps1` already compiles an `.iss`, point it at `{slug}-setup.iss` and pass `/DMyAppVersion=$Version`. Leave the rest of the packager alone unless the user asked to change the build.

Compile only when the user asks to build. `ISCC.exe` is `Inno Setup 6\ISCC.exe` under Program Files (x86), then Program Files.

## Do not

- Copy product names, GUIDs, ports, or service names from a different repo into this one.
- Commit unless the user asks.
