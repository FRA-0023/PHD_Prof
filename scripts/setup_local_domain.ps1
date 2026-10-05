# setup_local_domain.ps1
# Configures local domain 'phdprof.test' pointing to 127.0.0.1 in Windows hosts file.
$hostsPath = Join-Path $env:SystemRoot "System32\drivers\etc\hosts"

if (-not (Test-Path $hostsPath)) {
    Write-Error "File hosts non trovato in $hostsPath"
    exit 1
}

$content = Get-Content -Path $hostsPath -Raw
if ($content -match "(?m)^\s*127\.0\.0\.1\s+phdprof\.test\b") {
    Write-Host "[OK] phdprof.test e' gia' configurato nel file hosts." -ForegroundColor Green
} else {
    Write-Host "[*] Aggiunta di phdprof.test a $hostsPath..." -ForegroundColor Cyan
    Add-Content -Path $hostsPath -Value "`r`n127.0.0.1       phdprof.test" -Encoding UTF8
    Write-Host "[OK] phdprof.test aggiunto con successo." -ForegroundColor Green
}

# Flush DNS resolver cache
ipconfig /flushdns | Out-Null
Write-Host "[OK] Cache DNS svuotata." -ForegroundColor Green
