# What the Windows installer does

Reading this before you paste? Good. Here's what happens.

The install script is one file, plain PowerShell, no obfuscation. Read it: [install.ps1](install.ps1).

## Before you start

- **Supported Windows:** Windows 10 build 1809 (October 2018) or newer, and all of Windows 11.
- **PowerShell:** the one that ships with Windows (5.1) is fine. PowerShell 7 (Core) works too.
- **Terminal:** Windows Terminal, the blue PowerShell console, or the new Terminal Preview — all fine.
- **Admin rights:** not required for the script itself. winget may prompt for UAC during a specific install.

## The command

```powershell
iex (iwr -useb https://raw.githubusercontent.com/botz-pillar/applybrief/main/install.ps1).Content
```

Paste into PowerShell. Hit Enter.

## What it does, step by step

1. **Confirms you're on a supported Windows version.**
2. **Checks for winget** (Microsoft's package manager — ships in "App Installer" from the Store). If missing, tells you exactly how to get it and exits.
3. **Checks for Python 3.11 or newer.** Installs `Python.Python.3.12` via winget if missing. You may see a UAC prompt — click Yes.
4. **Checks for pipx.** Installs via `python -m pip install --user pipx`, then runs `pipx ensurepath` so `applybrief` lands on your PATH in new windows.
5. **1Password CLI hint** (optional). Prints how to enable it inside the 1Password desktop app and continues.
6. **Installs ApplyBrief** from a pinned GitHub tag with `pipx install git+https://github.com/botz-pillar/applybrief.git@v0.1.0`.
7. **Runs `applybrief doctor`** to verify everything works.

## What you'll see

- Maybe an **execution policy** warning. The recommended one-liner runs in-memory, which bypasses file-execution policy. If you saved the script and ran it directly, you'd need `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first (resets when you close the window).
- One or more **UAC prompts** when winget installs Python — click Yes.
- A note from pipx about PATH. New PowerShell windows will pick up the change.

## What it does NOT do

- It does not change your `$PROFILE` or any global PowerShell settings.
- It does not collect telemetry. No phone-home.
- It does not ask for your email, your résumé, or any personal info — that happens later when you run `applybrief init`.

## If you want to be paranoid

`.\install.ps1 -DryRun` prints every command it would run, changing nothing.

## Fallback: WSL2

Older Windows that can't run winget, or you prefer the Linux flow? Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) + Ubuntu, then use the Mac/Linux installer. Documented fallback, not deprecated.

## If something breaks

The script prints which step failed, a GitHub issues link, and my direct email (josh@pillarsecurity.io). I read every one. You will not be left stuck.
