@echo off
setlocal EnableDelayedExpansion
title Configure Local Domain phdprof.test

set "HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts"

:: Verify administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [i] Requesting administrator privileges to edit hosts file...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Elevated execution environment
cd /d "%~dp0"
echo ==============================================================================
echo   Configure Local Domain: phdprof.test -^> 127.0.0.1
echo ==============================================================================
echo.

findstr /I /C:"phdprof.test" "%HOSTS_FILE%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] phdprof.test is already present in hosts file:
    findstr /I /C:"phdprof.test" "%HOSTS_FILE%"
) else (
    echo [*] Adding '127.0.0.1   phdprof.test' to %HOSTS_FILE%...
    echo.>>"%HOSTS_FILE%"
    echo 127.0.0.1       phdprof.test>>"%HOSTS_FILE%"
    if %errorlevel% equ 0 (
        echo [OK] Domain phdprof.test successfully registered!
    ) else (
        echo [ERROR] Failed to write to %HOSTS_FILE%.
    )
)

echo.
echo [*] Checking / Generating local SSL certificates...
if not exist "%~dp0certs\server.crt" (
    python "%~dp0scripts\generate_certificates.py"
)

if exist "%~dp0certs\ca.crt" (
    echo [*] Installing local Root CA into Windows Trusted Root Certificate Store...
    certutil -addstore -f Root "%~dp0certs\ca.crt"
    if !errorlevel! equ 0 (
        echo [OK] Root CA certificate successfully registered.
    ) else (
        echo [!] Fallback: Importing via PowerShell...
        powershell -NoProfile -Command "Import-Certificate -FilePath '%~dp0certs\ca.crt' -CertStoreLocation Cert:\LocalMachine\Root"
    )
)

echo.
echo [*] Flushing DNS resolver cache (ipconfig /flushdns)...
ipconfig /flushdns >nul
echo [OK] DNS cache successfully refreshed.
echo.
echo ==============================================================================
echo   Setup completed successfully!
echo   IMPORTANT: Restart your browser or open a new window to load the new root CA.
echo   Then navigate to: https://phdprof.test/
echo ==============================================================================
echo.
pause
