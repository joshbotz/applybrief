#!/usr/bin/env bash
#
# applybrief installer
# Usage:  curl -fsSL https://raw.githubusercontent.com/botz-pillar/applybrief/main/install.sh | bash
#         curl -fsSL https://raw.githubusercontent.com/botz-pillar/applybrief/main/install.sh | bash -s -- --dry-run
#
# What this does, in plain English:
#   1. Confirms you are on a Mac.
#   2. Checks for Homebrew. Offers to install if missing.
#   3. Checks for Python 3.11 or newer. Installs via Homebrew if missing.
#   4. Checks for pipx (a safe way to install Python tools). Installs via Homebrew if missing.
#   5. Checks for the 1Password CLI (op). Optional — prints manual install instructions if missing.
#   6. Installs applybrief itself from a pinned GitHub release tag using pipx.
#
# If anything fails, the script stops and prints exactly what went wrong
# plus how to get help. Nothing silent.

set -euo pipefail

# ---- config ----------------------------------------------------------------

readonly REQUIRED_PYTHON_MAJOR=3
readonly REQUIRED_PYTHON_MINOR=11
readonly PACKAGE_NAME="applybrief"
readonly APPLYBRIEF_VERSION="v0.1.0"
readonly INSTALL_SPEC="git+https://github.com/botz-pillar/applybrief.git@${APPLYBRIEF_VERSION}"
readonly ISSUES_URL="https://github.com/botz-pillar/applybrief/issues"
readonly SUPPORT_EMAIL="josh@pillarsecurity.io"

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help)
            cat <<EOF
applybrief installer

Usage:
  bash install.sh            Install applybrief.
  bash install.sh --dry-run  Show what would happen, don't change anything.
  bash install.sh --help     This message.
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

# ---- pretty printing -------------------------------------------------------

say()  { printf '\n==> %s\n' "$*"; }
info() { printf '    %s\n' "$*"; }
warn() { printf '    [warning] %s\n' "$*" >&2; }
err()  { printf '\n[error] %s\n' "$*" >&2; }

run() {
    # run <description> -- <command...>
    local desc="$1"; shift
    if [ "$1" != "--" ]; then
        err "internal: run() expected '--' after description"
        exit 99
    fi
    shift
    info "$desc"
    if [ "$DRY_RUN" -eq 1 ]; then
        info "  (dry-run) would execute: $*"
        return 0
    fi
    "$@"
}

print_help_and_exit() {
    local failing_step="$1"
    cat >&2 <<EOF

------------------------------------------------------------
Something went wrong during: ${failing_step}

If you are stuck:
  - Open an issue (include the lines above): ${ISSUES_URL}
  - Or email Josh directly: ${SUPPORT_EMAIL}

He will help you. This tool exists for people who are stressed
about job searching — you will not get left hanging.
------------------------------------------------------------
EOF
    exit 1
}

# ---- preflight: OS check ---------------------------------------------------

check_macos() {
    say "Checking your operating system..."
    if [ "$(uname -s)" != "Darwin" ]; then
        err "applybrief installer only supports macOS right now. Detected: $(uname -s)"
        print_help_and_exit "OS check"
    fi
    info "You are on macOS. Good."
}

# ---- step 1: Homebrew ------------------------------------------------------

source_brew_if_present() {
    if ! command -v brew >/dev/null 2>&1; then
        if [ -x /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -x /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
}

install_homebrew() {
    say "Checking for Homebrew (the Mac package manager)..."
    source_brew_if_present
    if command -v brew >/dev/null 2>&1; then
        info "Great, Homebrew is installed."
        return 0
    fi

    info "Homebrew is not installed. applybrief needs it to install Python and pipx."
    info "The official installer will run next: https://brew.sh"
    if [ "$DRY_RUN" -eq 1 ]; then
        info "  (dry-run) would prompt for Homebrew install and run the official script."
        return 0
    fi

    printf "    Install Homebrew now? [y/N] "
    read -r reply </dev/tty || reply="n"
    case "$reply" in
        y|Y|yes|YES)
            if ! /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
                err "Homebrew installer failed."
                print_help_and_exit "Homebrew install"
            fi
            source_brew_if_present
            ;;
        *)
            err "Cannot continue without Homebrew."
            print_help_and_exit "Homebrew install (declined)"
            ;;
    esac
}

# ---- step 2: Python --------------------------------------------------------

python_version_ok() {
    local py="$1"
    "$py" -c "import sys; sys.exit(0 if sys.version_info >= (${REQUIRED_PYTHON_MAJOR}, ${REQUIRED_PYTHON_MINOR}) else 1)" 2>/dev/null
}

install_python() {
    say "Checking for Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR}+..."
    local found=""
    for candidate in python3.13 python3.12 python3.11 python3; do
        if command -v "$candidate" >/dev/null 2>&1 && python_version_ok "$candidate"; then
            found="$candidate"
            break
        fi
    done

    if [ -n "$found" ]; then
        local version
        version="$("$found" --version 2>&1 | awk '{print $2}')"
        info "Great, you have Python ${version}."
        return 0
    fi

    info "No Python ${REQUIRED_PYTHON_MAJOR}.${REQUIRED_PYTHON_MINOR}+ found. Installing via Homebrew."
    if ! run "brew install python@3.13" -- brew install python@3.13; then
        err "Homebrew failed to install Python."
        print_help_and_exit "Python install"
    fi
}

# ---- step 3: pipx ----------------------------------------------------------

install_pipx() {
    say "Checking for pipx (safe installer for Python command-line tools)..."
    if command -v pipx >/dev/null 2>&1; then
        info "Great, pipx is installed."
        return 0
    fi
    info "pipx is not installed. Installing via Homebrew."
    if ! run "brew install pipx" -- brew install pipx; then
        err "Homebrew failed to install pipx."
        print_help_and_exit "pipx install"
    fi
    if ! run "pipx ensurepath" -- pipx ensurepath; then
        warn "pipx ensurepath returned non-zero."
        warn "Open a new Terminal window after this install finishes, then run: applybrief init"
    fi
}

# ---- step 4: 1Password CLI (optional) --------------------------------------

check_1password_cli() {
    say "Checking for 1Password CLI (optional — used if you store API keys in 1Password)..."
    if command -v op >/dev/null 2>&1; then
        info "Great, 1Password CLI is installed."
        return 0
    fi
    info "1Password CLI not found. This is optional — applybrief works without it."
    info "If you want it later, install from: https://developer.1password.com/docs/cli/get-started/"
    info "Or: brew install --cask 1password-cli"
}

# ---- step 5: applybrief itself ---------------------------------------------

install_applybrief() {
    say "Installing applybrief (${APPLYBRIEF_VERSION}) from GitHub..."
    if ! run "pipx install ${INSTALL_SPEC}" -- pipx install "${INSTALL_SPEC}"; then
        err "pipx failed to install ${PACKAGE_NAME} from ${INSTALL_SPEC}."
        info "You can retry by hand: pipx install ${INSTALL_SPEC}"
        print_help_and_exit "applybrief install"
    fi
}

# ---- final message ---------------------------------------------------------

print_success() {
    cat <<EOF

------------------------------------------------------------
applybrief is installed.

Next steps:
  1. Open a new Terminal window (so your PATH picks up pipx).
  2. applybrief init        — set up your profile (takes about 5 minutes)
  3. applybrief discover    — find jobs worth your time
  4. applybrief apply <url> — go deep on one role

If 'applybrief' is not found after opening a new Terminal,
run: pipx ensurepath  — then open another new Terminal.

Questions or stuck? ${SUPPORT_EMAIL}
------------------------------------------------------------
EOF
}

# ---- main ------------------------------------------------------------------

main() {
    if [ "$DRY_RUN" -eq 1 ]; then
        say "DRY RUN — no changes will be made."
    fi
    check_macos
    install_homebrew
    install_python
    install_pipx
    check_1password_cli
    install_applybrief
    if [ "$DRY_RUN" -eq 0 ]; then
        print_success
    else
        say "Dry run complete. Re-run without --dry-run to actually install."
    fi
}

main "$@"
