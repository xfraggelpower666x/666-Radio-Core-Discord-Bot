param(
  [string]$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
)

$ErrorActionPreference = "Stop"

function Write-Check {
  param(
    [string]$Name,
    [bool]$Ok,
    [string]$Info = ""
  )

  $status = if ($Ok) { "OK" } else { "FEHLT" }
  $line = "[{0}] {1}" -f $status, $Name
  if ($Info) { $line = "$line - $Info" }
  Write-Host $line
}

function Read-DotEnv {
  param([string]$Path)

  $values = @{}
  if (-not (Test-Path -LiteralPath $Path)) {
    return $values
  }

  Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }
    $parts = $line.Split("=", 2)
    $values[$parts[0].Trim()] = $parts[1].Trim()
  }

  return $values
}

$botDir = Join-Path $RepoRoot "Discord-Bot\666-RadioBotAI"
$workerFile = Join-Path $RepoRoot "Arbeiter\src\index.js"
$adminWorkerFile = Join-Path $RepoRoot "Workers\666myidjstreamadmin\src\index.js"
$settingsFile = Join-Path $botDir "settings.json"
$envExampleFile = Join-Path $botDir ".env.example"
$envFile = Join-Path $botDir ".env"

Write-Host "666 RadioBotAI Readiness Check"
Write-Host "Repo: $RepoRoot"
Write-Host ""

Write-Check "Bot-Verzeichnis" (Test-Path -LiteralPath $botDir) $botDir
Write-Check "settings.json" (Test-Path -LiteralPath $settingsFile) "wird vom Bot beim Start gelesen"
Write-Check ".env.example" (Test-Path -LiteralPath $envExampleFile) "Vorlage fuer lokale Secrets"
Write-Check ".env" (Test-Path -LiteralPath $envFile) "muss lokal aus .env.example erstellt werden"

$env = Read-DotEnv $envFile
Write-Host ""
Write-Host "Pflichtwerte in .env:"
foreach ($key in @("DISCORD_TOKEN", "DISCORD_CLIENT_ID", "RADIO_STREAM_URL")) {
  $isSet = $env.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($env[$key])
  Write-Check $key $isSet
}

Write-Host ""
Write-Host "Optionale PHASE2C Worker-Bridge:"
foreach ($key in @("RADIOBOTAI_WORKER_URL", "RADIOBOTAI_ADMIN_TOKEN")) {
  $isSet = $env.ContainsKey($key) -and -not [string]::IsNullOrWhiteSpace($env[$key])
  Write-Check $key $isSet "nur fuer /radioaddon Admin-Aktionen noetig"
}

Write-Host ""
Write-Host "Lokale Tools:"
Write-Check "python" ([bool](Get-Command python -ErrorAction SilentlyContinue))
Write-Check "node" ([bool](Get-Command node -ErrorAction SilentlyContinue))
Write-Check "docker" ([bool](Get-Command docker -ErrorAction SilentlyContinue)) "Docker Desktop muss installiert und im PATH sein"

Write-Host ""
Write-Host "Syntax Checks:"
if (Get-Command node -ErrorAction SilentlyContinue) {
  node --check $workerFile | Out-Null
  Write-Check "Arbeiter Worker JS" $true
  node --check $adminWorkerFile | Out-Null
  Write-Check "Admin Worker JS" $true
} else {
  Write-Check "Worker JS Syntax" $false "node fehlt"
}

if (Get-Command python -ErrorAction SilentlyContinue) {
  Push-Location $botDir
  try {
    python -m py_compile `
      ".\main.py" `
      ".\voicelink\config.py" `
      ".\cogs\radio.py" `
      ".\cogs\radiobotai_addons.py" `
      ".\radiobotai_ai_client.py" `
      ".\radiobotai_permissions.py" `
      ".\radiobotai_presets.py" `
      ".\radiobotai_runtime_status.py"
    Write-Check "Bot Python Syntax" $true
  } finally {
    Pop-Location
  }
} else {
  Write-Check "Bot Python Syntax" $false "python fehlt"
}

Write-Host ""
Write-Host "Naechster Start:"
Write-Host "  cd `"$botDir`""
Write-Host "  copy .env.example .env"
Write-Host "  notepad .env"
Write-Host "  docker compose up -d --build"
Write-Host "  docker compose logs -f bot"
