# What the Mac installer does

Reading this before you paste? Good. Here's what happens.

The install script is one file, plain bash, no obfuscation. Read it: [install.sh](install.sh).

## The command

```
curl -fsSL https://raw.githubusercontent.com/joshbotz/applybrief/main/install.sh | bash
```

Paste into Terminal. Hit Enter.

## What it does, step by step

1. **Confirms you're on a Mac.** Stops cleanly if not.
2. **Checks for Homebrew** (the Mac package manager). Asks before installing if it's missing.
3. **Checks for Python 3.11 or newer.** Installs `python@3.13` via Homebrew if missing.
4. **Checks for pipx** (a safe way to install Python command-line tools). Installs via Homebrew if missing, then runs `pipx ensurepath` so `applybrief` lands on your PATH.
5. **Checks for the 1Password CLI** (optional). Prints how to install it if you want, then continues.
6. **Installs ApplyBrief** from a pinned GitHub tag with `pipx install git+https://github.com/joshbotz/applybrief.git@v0.1.0`.

## What it does NOT do

- It does not change your shell config (`.zshrc`, `.bash_profile`) except via `pipx ensurepath`.
- It does not collect telemetry. No phone-home.
- It does not ask for your email, your résumé, or any personal info — that happens later when you run `applybrief init`.

## If you want to be paranoid

`bash install.sh --dry-run` prints every command it would run, changing nothing.

## If something breaks

The script prints which step failed, a GitHub issues link, and my direct email (josh@pillarsecurity.io). I read every one. You will not be left stuck.
