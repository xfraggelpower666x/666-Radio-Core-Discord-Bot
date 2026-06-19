param(
  [switch]$SkipHelloWorld
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "[ChatAI Docker Setup] $Message" -ForegroundColor Cyan
}

function Write-Ok {
  param([string]$Message)
  Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
  param([string]$Message)
  Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Test-Admin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($identity)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Restart-AsAdmin {
  $script = $PSCommandPath
  $args = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$script`"")
  if ($SkipHelloWorld) {
    $args += "-SkipHelloWorld"
  }

  Write-Warn "Dieses Skript braucht Administratorrechte. Starte neu als Administrator..."
  Start-Process powershell.exe -Verb RunAs -ArgumentList $args
  exit 0
}

function Enable-WindowsFeatureSafe {
  param([string]$FeatureName)

  Write-Step "Aktiviere Windows Feature: $FeatureName"
  $result = Start-Process dism.exe `
    -ArgumentList "/online", "/enable-feature", "/featurename:$FeatureName", "/all", "/norestart" `
    -Wait `
    -PassThru `
    -WindowStyle Hidden

  if ($result.ExitCode -eq 0 -or $result.ExitCode -eq 3010) {
    Write-Ok "$FeatureName ist aktiviert oder war bereits aktiv."
    return $result.ExitCode
  }

  throw "DISM konnte $FeatureName nicht aktivieren. ExitCode: $($result.ExitCode)"
}

function Get-CommandPath {
  param([string]$Name)
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

function Start-DockerDesktop {
  $candidates = @(
    "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
  )

  foreach ($path in $candidates) {
    if ($path -and (Test-Path -LiteralPath $path)) {
      Write-Step "Starte Docker Desktop"
      Start-Process -FilePath $path -WindowStyle Hidden
      return $true
    }
  }

  return $false
}

function Wait-DockerDaemon {
  param([int]$Seconds = 90)

  Write-Step "Warte auf Docker Engine"
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    try {
      docker info *> $null
      Write-Ok "Docker Engine laeuft."
      return $true
    } catch {
      Start-Sleep -Seconds 3
    }
  }

  Write-Warn "Docker Engine ist noch nicht bereit. Oeffne Docker Desktop oder starte Windows neu."
  return $false
}

if (-not (Test-Admin)) {
  Restart-AsAdmin
}

Write-Host "============================================================"
Write-Host " ChatAI Docker Desktop Installer fuer 666 RadioBotAI"
Write-Host "============================================================"

Write-Step "Pruefe Windows/WSL Voraussetzungen"
$restartNeeded = $false
$code = Enable-WindowsFeatureSafe "Microsoft-Windows-Subsystem-Linux"
if ($code -eq 3010) { $restartNeeded = $true }
$code = Enable-WindowsFeatureSafe "VirtualMachinePlatform"
if ($code -eq 3010) { $restartNeeded = $true }

if (Get-CommandPath "wsl.exe") {
  Write-Step "Aktualisiere WSL und setze WSL 2 als Standard"
  try { wsl --update } catch { Write-Warn "WSL Update konnte nicht abgeschlossen werden: $($_.Exception.Message)" }
  try { wsl --set-default-version 2 } catch { Write-Warn "WSL Default-Version konnte nicht gesetzt werden: $($_.Exception.Message)" }
  Write-Ok "WSL Check abgeschlossen."
} else {
  Write-Warn "wsl.exe wurde nicht gefunden. Nach einem Neustart erneut ausfuehren."
  $restartNeeded = $true
}

Write-Step "Pruefe Docker Desktop"
$dockerPath = Get-CommandPath "docker.exe"
if ($dockerPath) {
  Write-Ok "Docker CLI ist bereits vorhanden: $dockerPath"
} else {
  $wingetPath = Get-CommandPath "winget.exe"
  if (-not $wingetPath) {
    Write-Warn "winget ist nicht verfuegbar. Oeffne die offizielle Docker Desktop Download-Seite."
    Start-Process "https://docs.docker.com/desktop/setup/install/windows-install/"
    Write-Host ""
    Write-Host "Installiere Docker Desktop manuell und fuehre danach dieses Skript erneut aus."
    exit 1
  }

  Write-Step "Installiere Docker Desktop per winget"
  winget install --id Docker.DockerDesktop -e --source winget --accept-source-agreements --accept-package-agreements
}

if ($restartNeeded) {
  Write-Warn "Windows Features wurden geaendert. Ein Neustart ist wahrscheinlich noetig."
}

$started = Start-DockerDesktop
if (-not $started) {
  Write-Warn "Docker Desktop wurde installiert, aber die EXE wurde nicht automatisch gefunden. Bitte ueber Startmenue oeffnen."
}

$daemonReady = Wait-DockerDaemon -Seconds 90

Write-Step "Versionen"
try { docker --version } catch { Write-Warn "docker --version fehlgeschlagen." }
try { docker compose version } catch { Write-Warn "docker compose version fehlgeschlagen." }

if ($daemonReady -and -not $SkipHelloWorld) {
  Write-Step "Teste Docker mit hello-world"
  docker run hello-world
}

Write-Step "Naechster Schritt fuer 666 RadioBotAI"
$repoRoot = Resolve-Path "$PSScriptRoot\.."
$botDir = Join-Path $repoRoot "Discord-Bot\666-RadioBotAI"
Write-Host "cd `"$botDir`""
Write-Host "copy .env.example .env"
Write-Host "notepad .env"
Write-Host "docker compose up -d --build"
Write-Host "docker compose logs -f bot"

Write-Host ""
Write-Ok "ChatAI Docker Setup ist fertig. Falls Docker noch nicht antwortet: Windows neu starten und Docker Desktop oeffnen."
