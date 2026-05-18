Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $repoRoot '.env'

if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Error "Nie znaleziono pliku .env w: $repoRoot"
}

Get-Content -LiteralPath $envFile | ForEach-Object {
    $line = $_.Trim()

    if (-not $line -or $line.StartsWith('#')) {
        return
    }

    $parts = $line -split '=', 2
    if ($parts.Count -ne 2) {
        return
    }

    $name = $parts[0].Trim()
    $value = $parts[1].Trim()

    if ($name) {
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
        Set-Item -Path "Env:$name" -Value $value
    }
}

$localBin = if (-not [string]::IsNullOrWhiteSpace($env:LOCAL_BIN)) {
    $env:LOCAL_BIN
} else {
    $env:SKW_LOCAL_BIN
}
if (-not [string]::IsNullOrWhiteSpace($localBin)) {
    if ([string]::IsNullOrWhiteSpace($env:PATH)) {
        $env:PATH = $localBin
    } elseif ($env:PATH -notlike "*${localBin}*") {
        $env:PATH = "$env:PATH;$localBin"
    }
}

if ([string]::IsNullOrWhiteSpace($env:HTTPS_PROXY) -or [string]::IsNullOrWhiteSpace($env:HTTP_PROXY)) {
    Write-Warning "Brak HTTPS_PROXY lub HTTP_PROXY w środowisku. Pobieranie pakietów przez proxy może nie działać poprawnie."
}

Write-Host "Załadowano zmienne z .env (scope: process)."
Write-Host "Ustawiono proxy i PATH dla bieżącej sesji."
Write-Host "Uruchamiam VS Code w katalogu repozytorium..."

Set-Location -LiteralPath $repoRoot
code .
