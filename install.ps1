<#
.SYNOPSIS
    applybrief Windows installer.

.DESCRIPTION
    Installs applybrief on Windows 10 (build 1809+) and Windows 11.

    What this does, in plain English:
      1. Confirms you are on a supported Windows version.
      2. Checks for winget (the Windows package manager). If missing, tells
         you exactly how to get it from the Microsoft Store and exits.
      3. Checks for Python 3.11 or newer. Installs via winget if missing.
      4. Checks for pipx (a safe way to install Python tools). Installs via
         python -m pip if missing, then runs pipx ensurepath.
      5. Notes the optional 1Password CLI hint for Windows.
      6. Installs applybrief itself from a pinned GitHub release tag using pipx.
      7. Runs 'applybrief doctor' to verify the install.

    If anything fails, the script stops and prints exactly what went wrong
    plus how to get help. Nothing silent.

.PARAMETER DryRun
    Show every step the script would take without making any changes.

.EXAMPLE
    iex (iwr -useb https://raw.githubusercontent.com/botz-pillar/applybrief/main/install.ps1).Content

    Standard install via paste-and-run.

.EXAMPLE
    .\install.ps1 -DryRun

    Print every action the installer would take. Modifies nothing.

.NOTES
    Author: Josh Botz <josh@pillarsecurity.io>
    Issues: https://github.com/botz-pillar/applybrief/issues
#>

#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$DryRun
)

# ---- config ----------------------------------------------------------------

$script:PackageName       = 'applybrief'
$script:ApplybriefVersion = 'v0.1.0'
$script:InstallSpec       = "git+https://github.com/botz-pillar/applybrief.git@$script:ApplybriefVersion"
$script:RequiredPyMajor   = 3
$script:RequiredPyMinor   = 11
$script:IssuesUrl         = 'https://github.com/botz-pillar/applybrief/issues'
$script:SupportEmail      = 'josh@pillarsecurity.io'
$script:MinWin10Build     = 17763   # Windows 10 1809

# ---- pretty printing -------------------------------------------------------

function Say  { param([string]$Msg) Write-Host ""; Write-Host "==> $Msg" -ForegroundColor Cyan }
function Info { param([string]$Msg) Write-Host "    $Msg" }
function Warn { param([string]$Msg) Write-Warning $Msg }
function Err  { param([string]$Msg) Write-Host ""; Write-Host "[error] $Msg" -ForegroundColor Red }

function Invoke-Step {
    param(
        [Parameter(Mandatory)][string]$Description,
        [Parameter(Mandatory)][scriptblock]$Action
    )
    Info $Description
    if ($DryRun) {
        Info "  (dry-run) would execute: $($Action.ToString().Trim())"
        return
    }
    & $Action
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        throw "Command exited with code $LASTEXITCODE."
    }
}

function Stop-WithHelp {
    param([string]$FailingStep, [string]$Detail = '')
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Something went wrong during: $FailingStep" -ForegroundColor Yellow
    if ($Detail) { Write-Host $Detail -ForegroundColor Yellow }
    Write-Host ""
    Write-Host "If you are stuck:" -ForegroundColor Yellow
    Write-Host "  - Open an issue (include the lines above): $script:IssuesUrl" -ForegroundColor Yellow
    Write-Host "  - Or email Josh directly: $script:SupportEmail" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "He will help you. This tool exists for people who are stressed" -ForegroundColor Yellow
    Write-Host "about job searching -- you will not get left hanging." -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    exit 1
}

# ---- preflight: OS check ---------------------------------------------------

function Test-WindowsVersion {
    Say "Checking your operating system..."
    if (-not $IsWindows -and $PSVersionTable.PSVersion.Major -ge 6) {
        Err "applybrief Windows installer only runs on Windows. Detected non-Windows host."
        Info "On macOS, use the Mac installer (install.sh)."
        Info "On Linux, the recommended path today is WSL2 on Windows; no native Linux install yet."
        Stop-WithHelp "OS check"
    }

    try {
        $os    = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
        $build = [int]($os.BuildNumber)
    } catch {
        Err "Could not read your Windows version: $($_.Exception.Message)"
        Stop-WithHelp "OS check"
    }

    if ($build -lt $script:MinWin10Build) {
        Err "applybrief needs Windows 10 build $script:MinWin10Build (October 2018 / version 1809) or newer."
        Info "Detected build: $build"
        Info ""
        Info "Two options:"
        Info "  1. Update Windows: Settings -> Update & Security -> Check for updates."
        Info "  2. Use WSL2 (Windows Subsystem for Linux) and run the Linux/Mac flow there."
        Info "     See: https://learn.microsoft.com/en-us/windows/wsl/install"
        Stop-WithHelp "OS check"
    }

    Info "You are on Windows build $build. Good."
}

# ---- step 1: winget --------------------------------------------------------

function Test-Winget {
    Say "Checking for winget (the Windows package manager)..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info "Great, winget is installed."
        return
    }

    Err "winget is not installed."
    Info ""
    Info "winget ships inside the 'App Installer' package from the Microsoft Store."
    Info "To get it:"
    Info "  1. Open Microsoft Store (Start menu -> type 'Microsoft Store')."
    Info "  2. Search for: App Installer"
    Info "  3. Click 'Get' or 'Update'."
    Info "  4. Open a new PowerShell window and re-run this installer."
    Info ""
    Info "Direct link: https://aka.ms/getwinget"
    Stop-WithHelp "winget check"
}

# ---- step 2: Python --------------------------------------------------------

function Test-PythonVersionOk {
    param([string]$PythonExe)
    try {
        & $PythonExe -c "import sys; sys.exit(0 if sys.version_info >= ($script:RequiredPyMajor, $script:RequiredPyMinor) else 1)" 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Find-Python {
    foreach ($candidate in @('python3.13','python3.12','python3.11','python3','python','py')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }

        $exe = if ($candidate -eq 'py') { 'py' } else { $cmd.Source }
        if ($candidate -eq 'py') {
            try { & py -3 -c "import sys; sys.exit(0 if sys.version_info >= ($script:RequiredPyMajor, $script:RequiredPyMinor) else 1)" 2>$null } catch {}
            if ($LASTEXITCODE -eq 0) { return @{ Exe = 'py'; Args = @('-3') } }
            continue
        }

        if (Test-PythonVersionOk -PythonExe $exe) {
            return @{ Exe = $exe; Args = @() }
        }
    }
    return $null
}

function Install-Python {
    Say "Checking for Python $script:RequiredPyMajor.$script:RequiredPyMinor+..."
    $found = Find-Python
    if ($found) {
        $verArgs = $found.Args + @('--version')
        $version = & $found.Exe @verArgs 2>&1
        Info "Great, you have $version (at $($found.Exe))."
        return $found
    }

    Info "No Python $script:RequiredPyMajor.$script:RequiredPyMinor+ found. Installing via winget."
    Info "Package: Python.Python.3.12"
    Info ""
    Info "You may see a UAC (User Account Control) prompt asking permission to install."
    Info "Click 'Yes' to continue."

    try {
        Invoke-Step "winget install Python.Python.3.12" {
            winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
        }
    } catch {
        Err "winget failed to install Python: $($_.Exception.Message)"
        Info "You can install Python by hand from: https://www.python.org/downloads/windows/"
        Stop-WithHelp "Python install"
    }

    if ($DryRun) { return @{ Exe = 'python'; Args = @() } }

    $env:PATH = [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH','User')
    $found = Find-Python
    if (-not $found) {
        Err "Python installed but isn't on PATH in this shell."
        Info "Close this PowerShell window, open a new one, and re-run this installer."
        Stop-WithHelp "Python PATH"
    }
    Info "Python is now available at: $($found.Exe)"
    return $found
}

# ---- step 3: pipx ----------------------------------------------------------

function Install-Pipx {
    param([hashtable]$Python)

    Say "Checking for pipx (safe installer for Python command-line tools)..."
    if (Get-Command pipx -ErrorAction SilentlyContinue) {
        Info "Great, pipx is installed."
        return
    }

    Info "pipx is not installed. Installing via 'python -m pip install --user pipx'."
    $pyExe = $Python.Exe
    $pyArgs = $Python.Args

    try {
        Invoke-Step "$pyExe $($pyArgs -join ' ') -m pip install --user pipx" {
            & $pyExe @pyArgs -m pip install --user pipx
        }
    } catch {
        Err "pip failed to install pipx: $($_.Exception.Message)"
        Stop-WithHelp "pipx install"
    }

    try {
        Invoke-Step "$pyExe $($pyArgs -join ' ') -m pipx ensurepath" {
            & $pyExe @pyArgs -m pipx ensurepath
        }
    } catch {
        Warn "pipx ensurepath returned an error. Open a new PowerShell window after install, then run: applybrief doctor"
    }

    if (-not $DryRun) {
        $env:PATH = [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH','User')
    }
}

# ---- step 4: 1Password CLI hint --------------------------------------------

function Show-OnePasswordHint {
    Say "1Password CLI (optional)..."
    if (Get-Command op -ErrorAction SilentlyContinue) {
        Info "Great, 1Password CLI is installed."
        return
    }
    Info "1Password CLI ('op') is not installed. This is optional -- applybrief works without it."
    Info ""
    Info "If you want it: install the 1Password desktop app, then enable the CLI under"
    Info "  Settings -> Developer -> Command-Line Interface."
    Info "Otherwise you can paste API keys directly when 'applybrief init' asks."
}

# ---- step 5: applybrief itself ---------------------------------------------

function Install-Applybrief {
    param([hashtable]$Python)

    Say "Installing applybrief ($script:ApplybriefVersion) from GitHub..."
    $pyExe = $Python.Exe
    $pyArgs = $Python.Args

    if (Get-Command pipx -ErrorAction SilentlyContinue) {
        try {
            Invoke-Step "pipx install $script:InstallSpec" {
                pipx install $script:InstallSpec
            }
        } catch {
            Err "pipx failed to install $script:PackageName from $script:InstallSpec"
            Info "Retry by hand: pipx install $script:InstallSpec"
            Stop-WithHelp "applybrief install"
        }
    } else {
        try {
            Invoke-Step "$pyExe -m pipx install $script:InstallSpec" {
                & $pyExe @pyArgs -m pipx install $script:InstallSpec
            }
        } catch {
            Err "pipx (via python -m) failed to install $script:PackageName."
            Info "Retry by hand in a new PowerShell window: pipx install $script:InstallSpec"
            Stop-WithHelp "applybrief install"
        }
    }
}

# ---- step 6: verify --------------------------------------------------------

function Test-Applybrief {
    Say "Verifying install by running 'applybrief doctor'..."
    if ($DryRun) {
        Info "  (dry-run) would execute: applybrief doctor"
        return
    }

    $env:PATH = [Environment]::GetEnvironmentVariable('PATH','Machine') + ';' + [Environment]::GetEnvironmentVariable('PATH','User')

    if (-not (Get-Command applybrief -ErrorAction SilentlyContinue)) {
        Warn "'applybrief' is installed but isn't on PATH yet in this shell."
        Info "Open a new PowerShell window and run: applybrief doctor"
        return
    }

    try {
        applybrief doctor
    } catch {
        Warn "'applybrief doctor' reported an issue: $($_.Exception.Message)"
        Info "Open a new PowerShell window and run 'applybrief doctor' again."
    }
}

# ---- final message ---------------------------------------------------------

function Show-Success {
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Green
    Write-Host "applybrief is installed."                                     -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"                                                  -ForegroundColor Green
    Write-Host "  1. Open a new PowerShell or Windows Terminal window"        -ForegroundColor Green
    Write-Host "     (so your PATH picks up pipx-installed tools)."           -ForegroundColor Green
    Write-Host "  2. applybrief init        -- set up your profile (~5 min)" -ForegroundColor Green
    Write-Host "  3. applybrief discover    -- find jobs worth your time"    -ForegroundColor Green
    Write-Host "  4. applybrief apply <url> -- go deep on one role"          -ForegroundColor Green
    Write-Host ""
    Write-Host "If 'applybrief' is not found after opening a new window,"    -ForegroundColor Green
    Write-Host "run: python -m pipx ensurepath -- then open another window." -ForegroundColor Green
    Write-Host ""
    Write-Host "Questions or stuck? $script:SupportEmail"                    -ForegroundColor Green
    Write-Host "------------------------------------------------------------" -ForegroundColor Green
}

# ---- main ------------------------------------------------------------------

function Invoke-Main {
    if ($DryRun) {
        Say "DRY RUN -- no changes will be made."
    }

    Test-WindowsVersion
    Test-Winget
    $python = Install-Python
    Install-Pipx -Python $python
    Show-OnePasswordHint
    Install-Applybrief -Python $python
    Test-Applybrief

    if ($DryRun) {
        Say "Dry run complete. Re-run without -DryRun to actually install."
    } else {
        Show-Success
    }
}

try {
    Invoke-Main
} catch {
    Err "Unexpected failure: $($_.Exception.Message)"
    Stop-WithHelp "installer (unexpected)" -Detail $_.ScriptStackTrace
}
