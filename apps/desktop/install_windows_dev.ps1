# Dev install (no .exe) — Windows
# Creates a desktop shortcut that runs the launcher with your Python.

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
python -m pip install -q "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2" "pywebview>=5.0" "gradio>=4.44"

$launcher = Join-Path $Root "apps\desktop\launcher.py"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "BC Legal AI Associate.lnk"

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($shortcutPath)
$sc.TargetPath = (Get-Command python).Source
$sc.Arguments = "`"$launcher`""
$sc.WorkingDirectory = "$Root"
$sc.Description = "BC Legal AI Associate (local)"
$sc.Save()

Write-Host "Installed desktop shortcut: $shortcutPath"
Write-Host "Or run: python apps\desktop\launcher.py"
