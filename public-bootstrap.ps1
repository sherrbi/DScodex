param([switch]$InstallCodexCli)
$ErrorActionPreference = 'Stop'
# Public CLI prerequisite bootstrap, not DSCodex desktop replacement.
Write-Host 'Public source edition: original modified desktop and its assets are not included.'
if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows is required for this prepared target.' }
$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) {
    if (-not $InstallCodexCli) { throw 'Codex CLI absent. Review the official npm installation and rerun with -InstallCodexCli only if you approve network/package installation.' }
    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if (-not $npm) { throw 'Install Node.js/npm from its official source first. No software or credential is bundled.' }
    & $npm.Source install -g '@openai/codex'
    if ($LASTEXITCODE -ne 0) { throw 'Official Codex CLI installation failed.' }
    $codex = Get-Command codex -ErrorAction SilentlyContinue
    if (-not $codex) { throw 'Codex installed but not on this process PATH. Open a new terminal and retry.' }
}
& $codex.Source --version
if ($LASTEXITCODE -ne 0) { throw 'Codex CLI version check failed.' }
Write-Host 'CLI prerequisite verified only. DSCodex adapter/MCP/skills and desktop integration have not been reconstructed or accepted in this public edition.'
Write-Host 'Use your own authorized provider credentials. No credentials are copied or created by this script.'
# Do not launch the private ZIP scripts: their matching proprietary assets are absent.
