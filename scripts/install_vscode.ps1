# VS Code / Cursor: Proxy sicherstellen + Config fuer die Extension.
# Aufruf:
#   powershell -ExecutionPolicy Bypass -File scripts\install_vscode.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\install_vscode.ps1 -Workspace "C:\path\to\project" -UserSettings

param(
    [string]$Workspace = "",
    [switch]$UserSettings
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$GrokHome = Join-Path $env:USERPROFILE ".grok"
$ProxyDir = Join-Path $GrokHome "proxy"
$ConfigPath = Join-Path $GrokHome "config.toml"
$EnsurePy = Join-Path $ProxyDir "ensure_proxy.py"

New-Item -ItemType Directory -Force -Path $ProxyDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ProxyDir "logs") | Out-Null
Copy-Item -Force (Join-Path $RepoRoot "proxy\xai_filter_proxy.py") (Join-Path $ProxyDir "xai_filter_proxy.py")
Copy-Item -Force (Join-Path $RepoRoot "scripts\ensure_proxy.py") $EnsurePy

# --- config.toml endpoints ---
if (-not (Test-Path $ConfigPath)) {
    Copy-Item (Join-Path $RepoRoot "config\config.snippet.toml") $ConfigPath
    Write-Host "config.toml neu aus Snippet: $ConfigPath"
} else {
    $cfg = Get-Content $ConfigPath -Raw -ErrorAction SilentlyContinue
    if ($cfg -notmatch "cli_chat_proxy_base_url") {
        $block = @"

# Grok Privacy Filter - Chat ueber lokalen Proxy (VS Code Extension + CLI)
[endpoints]
cli_chat_proxy_base_url = "http://127.0.0.1:18743/v1"
"@
        Add-Content -Path $ConfigPath -Value $block
        Write-Host "endpoints an config.toml angehaengt."
    } else {
        Write-Host "config.toml hat cli_chat_proxy_base_url bereits."
    }
}

# --- Workspace tasks.json ---
if (-not $Workspace) {
    $Workspace = (Get-Location).Path
}
$Workspace = (Resolve-Path $Workspace).Path
$VsCodeDir = Join-Path $Workspace ".vscode"
$TasksPath = Join-Path $VsCodeDir "tasks.json"
New-Item -ItemType Directory -Force -Path $VsCodeDir | Out-Null

if (Test-Path $TasksPath) {
    Copy-Item -Force $TasksPath ($TasksPath + ".gpf-backup")
    Write-Host "Backup: $TasksPath.gpf-backup"
}

$ensureCmd = 'py -3 "' + $EnsurePy + '"'
$tasksJson = @"
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Grok Privacy: Ensure Filter Proxy",
      "type": "shell",
      "command": $($ensureCmd | ConvertTo-Json),
      "options": {
        "shell": {
          "executable": "cmd.exe",
          "args": ["/c"]
        }
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "silent",
        "panel": "dedicated",
        "showReuseMessage": false,
        "close": true
      },
      "runOptions": {
        "runOn": "folderOpen"
      }
    }
  ]
}
"@

# Merge other tasks from backup if possible
if (Test-Path ($TasksPath + ".gpf-backup")) {
    try {
        $prev = Get-Content ($TasksPath + ".gpf-backup") -Raw | ConvertFrom-Json
        $others = @()
        if ($prev.tasks) {
            $others = @($prev.tasks | Where-Object { $_.label -ne "Grok Privacy: Ensure Filter Proxy" })
        }
        if ($others.Count -gt 0) {
            $parts = New-Object System.Collections.Generic.List[string]
            $parts.Add(@"
    {
      "label": "Grok Privacy: Ensure Filter Proxy",
      "type": "shell",
      "command": $($ensureCmd | ConvertTo-Json),
      "options": {
        "shell": {
          "executable": "cmd.exe",
          "args": ["/c"]
        }
      },
      "problemMatcher": [],
      "presentation": {
        "reveal": "silent",
        "panel": "dedicated",
        "showReuseMessage": false,
        "close": true
      },
      "runOptions": {
        "runOn": "folderOpen"
      }
    }
"@)
            foreach ($t in $others) {
                $parts.Add((ConvertTo-Json $t -Depth 20))
            }
            $tasksJson = "{`n  `"version`": `"2.0.0`",`n  `"tasks`": [`n" + ($parts -join ",`n") + "`n  ]`n}`n"
            Write-Host ("Andere Tasks beibehalten: " + $others.Count)
        }
    } catch {
        Write-Warning "Merge anderer Tasks fehlgeschlagen - nur Ensure-Task geschrieben. Backup: tasks.json.gpf-backup"
    }
}

Set-Content -Path $TasksPath -Value $tasksJson -Encoding utf8
Write-Host "Workspace-Task geschrieben: $TasksPath"
Write-Host "  runOn=folderOpen - beim Oeffnen des Ordners laeuft ensure_proxy (wenn erlaubt)."

# --- User settings optional ---
if ($UserSettings) {
    $userSettingsCandidates = @(
        (Join-Path $env:APPDATA "Code\User\settings.json"),
        (Join-Path $env:APPDATA "Code - Insiders\User\settings.json"),
        (Join-Path $env:APPDATA "Cursor\User\settings.json")
    )
    foreach ($usp in $userSettingsCandidates) {
        $parent = Split-Path $usp -Parent
        if (-not (Test-Path $parent)) { continue }
        if (-not (Test-Path $usp)) {
            Set-Content -Path $usp -Value "{`r`n  `"task.allowAutomaticTasks`": `"on`"`r`n}`r`n" -Encoding utf8
            Write-Host "settings.json angelegt: $usp"
            continue
        }
        $raw = Get-Content $usp -Raw
        if ($raw -match "task\.allowAutomaticTasks") {
            Write-Host "task.allowAutomaticTasks bereits in $usp"
            continue
        }
        Copy-Item -Force $usp ($usp + ".gpf-backup")
        $trimmed = $raw.TrimEnd()
        if ($trimmed.EndsWith("}")) {
            $body = $trimmed.Substring(0, $trimmed.Length - 1).TrimEnd()
            if (-not $body.EndsWith("{") -and -not $body.EndsWith(",") -and $body.Length -gt 1) {
                $body = $body + ","
            }
            $newContent = $body + "`r`n  `"task.allowAutomaticTasks`": `"on`"`r`n}`r`n"
            Set-Content -Path $usp -Value $newContent -Encoding utf8
            Write-Host "task.allowAutomaticTasks ergaenzt: $usp"
        } else {
            Write-Warning "Konnte $usp nicht automatisch patchen - manuell task.allowAutomaticTasks=on setzen."
        }
    }
}

# Sofort Proxy sicherstellen
& py -3 $EnsurePy
Write-Host ""
Write-Host "=== VS Code / Extension ==="
Write-Host "1. Proxy: ensure_proxy ausgefuehrt."
Write-Host "2. Config: ~/.grok/config.toml endpoints.cli_chat_proxy_base_url = http://127.0.0.1:18743/v1"
Write-Host "3. In Grok: /new  oder VS Code Window Reload."
Write-Host "4. folderOpen-Task: automatische Tasks erlauben (oder task.allowAutomaticTasks=on)."
Write-Host "Details: docs/VSCODE.md"
