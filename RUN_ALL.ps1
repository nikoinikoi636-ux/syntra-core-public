$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PSScriptRoot
$py = "python"; try { $null = & $py -V } catch { $py = "py" }
& $py "heartcore_launcher.py" --smart-batch --stagger 1 --session heartcore
