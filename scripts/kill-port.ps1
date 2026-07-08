<#
.SYNOPSIS
    Znajduje proces blokujący podany port i opcjonalnie go zabija.
.EXAMPLE
    .\scripts\kill-port.ps1 8338
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [int]$Port
)

Write-Host "Szukam procesu na porcie $Port..." -ForegroundColor Cyan

$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "Port $Port jest wolny - zaden proces go nie blokuje." -ForegroundColor Green
    exit 0
}

foreach ($conn in $connections | Select-Object -Property OwningProcess -Unique) {
    $pid = $conn.OwningProcess
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue

    if ($proc) {
        Write-Host ""
        Writq`1ae-Host "Znaleziono proces blokujacy port ${Port}:" -ForegroundColor Yellow
        Write-Host "  PID:          $pid"
        Write-Host "  Nazwa:        $($proc.ProcessName)"
        Write-Host "  Sciezka:      $($proc.Path)"
        Write-Host "  Start:        $($proc.StartTime)"
        Write-Host "  Pamiec (MB):  $([math]::Round($proc.WorkingSet64 / 1MB, 1))"
        Write-Host ""

        $answer = Read-Host "Czy zabic ten proces? (t/n)"
        if ($answer -eq 't' -or $answer -eq 'T' -or $answer -eq 'tak') {
            Stop-Process -Id $pid -Force
            Write-Host "Proces $pid zakonczony." -ForegroundColor Green
        } else {
            Write-Host "Proces pozostawiony." -ForegroundColor Gray
        }
    } else {
        Write-Host "PID $pid - proces nie znaleziony (moze juz sie zakonczyl)." -ForegroundColor Gray
    }
}
