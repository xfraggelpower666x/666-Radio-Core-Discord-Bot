<#
 666RadioCoreDJ | start-666RadioCoreDJ.ps1
 Erstellt: 2026-06-03
 Geändert: 2026-06-03
 Zweck: Windows-Starthelfer für Installation, Slash-Command-Registrierung und Bot-Start.
 Hinweis: Secrets gehören in .env, nicht in dieses Skript.
#>
param(
  [switch]$Install,
  [switch]$RegisterCommands,
  [switch]$StartBot
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "=== 666RadioCoreDJ Windows Start ==="

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Erstellt: .env aus .env.example"
  Write-Host "Bitte .env öffnen und Discord-/Radio-Secrets eintragen. Danach Skript erneut starten."
  exit 0
}

if ($Install) {
  Write-Host "Installiere NPM-Abhängigkeiten..."
  npm install
}

if ($RegisterCommands) {
  Write-Host "Registriere Discord Slash Commands..."
  npm run register
}

if ($StartBot) {
  Write-Host "Starte 666RadioCoreDJ..."
  npm start
}

if (-not $Install -and -not $RegisterCommands -and -not $StartBot) {
  Write-Host "Keine Aktion gewählt. Beispiele:"
  Write-Host ".\start-666RadioCoreDJ.ps1 -Install"
  Write-Host ".\start-666RadioCoreDJ.ps1 -RegisterCommands"
  Write-Host ".\start-666RadioCoreDJ.ps1 -StartBot"
}
