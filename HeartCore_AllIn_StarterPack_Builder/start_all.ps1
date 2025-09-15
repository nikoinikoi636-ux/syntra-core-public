param(
  [switch]$DryRun = $false,
  [switch]$Yes = $false
)

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
$WS = Join-Path $ROOT "workspace"
$OUTDIR = Join-Path $WS "packs"
$LOGDIR = Join-Path $WS "logs"

if (!(Test-Path $OUTDIR)) {
  Write-Host "No packs found. Run ./install.sh (WSL) or extract zips manually to $OUTDIR."
  exit 1
}

New-Item -ItemType Directory -Force -Path $LOGDIR | Out-Null

function Launch-Cmd([string]$PackDir, [string]$Entry) {
  $Full = Join-Path $PackDir $Entry
  switch -regex ($Entry) {
    ".*\.ps1$" { "powershell -ExecutionPolicy Bypass -File `"$Full`""; break }
    ".*\.bat$" { "cmd /c `"$Full`""; break }
    ".*\.py$"  { "python `"$Full`""; break }
    ".*\.sh$"  { "wsl bash `"$Full`""; break }
    "Makefile" { "wsl make -C `"$PackDir`""; break }
    default    { ""; break }
  }
}

$packs = Get-ChildItem -Directory $OUTDIR | Sort-Object Name
foreach ($p in $packs) {
  $pack = $p.FullName
  $packname = $p.Name

  $candidates = @(
    (Get-ChildItem -Recurse -File -Path $pack -Include start*.ps1,start*.bat,start*.py,start*.sh  | Select-Object -First 1),
    (Get-ChildItem -Recurse -File -Path $pack -Include run*.ps1,run*.bat,run*.py,run*.sh        | Select-Object -First 1),
    (Get-ChildItem -Recurse -File -Path $pack -Include launch*.ps1,launch*.bat,launch*.py,launch*.sh | Select-Object -First 1),
    (Get-ChildItem -Recurse -File -Path $pack -Include main.py                                   | Select-Object -First 1),
    (Get-ChildItem -Recurse -File -Path $pack -Include Makefile                                  | Select-Object -First 1)
  ) | Where-Object { $_ -ne $null } | Select-Object -First 1

  if ($null -eq $candidates) {
    Write-Host "[?] No obvious entrypoint in $packname; skipping."
    continue
  }

  $rel = $candidates.FullName.Substring($pack.Length + 1)
  $cmd = Launch-Cmd $pack $rel

  if ([string]::IsNullOrWhiteSpace($cmd)) {
    Write-Host "[?] Unrecognized entrypoint type for $packname: $rel"
    continue
  }

  Write-Host "[>] $packname :: $rel"
  if ($DryRun) {
    Write-Host "    CMD: $cmd"
    continue
  }

  if (-not $Yes) {
    $ans = Read-Host "Start this module? [$packname] (y/N)"
    if ($ans.ToLower() -notin @("y","yes")) {
      Write-Host "    Skipped."
      continue
    }
  }

  $log = Join-Path $LOGDIR ("$packname-" + (Get-Date -Format "yyyy-MM-dd_HH-mm-ss") + ".log")
  Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-ExecutionPolicy Bypass -Command $cmd | Tee-Object -FilePath `"$log`""
}
Write-Host "[*] Launched. Logs in $LOGDIR"
