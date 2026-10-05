@echo off
setlocal EnableDelayedExpansion
title Configurazione Dominio Locale phdprof.test

set "HOSTS_FILE=%SystemRoot%\System32\drivers\etc\hosts"

:: Verifica privilegi di amministratore
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [i] Richiesta privilegi di amministratore per modificare il file hosts...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Ambiente con privilegi elevati
cd /d "%~dp0"
echo ==============================================================================
echo   Configurazione Dominio Locale: phdprof.test -^> 127.0.0.1
echo ==============================================================================
echo.

findstr /I /C:"phdprof.test" "%HOSTS_FILE%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] phdprof.test e' gia' presente nel file hosts:
    findstr /I /C:"phdprof.test" "%HOSTS_FILE%"
) else (
    echo [*] Aggiunta di '127.0.0.1   phdprof.test' a %HOSTS_FILE%...
    echo.>>"%HOSTS_FILE%"
    echo 127.0.0.1       phdprof.test>>"%HOSTS_FILE%"
    if %errorlevel% equ 0 (
        echo [OK] Dominio phdprof.test registrato con successo!
    ) else (
        echo [ERRORE] Impossibile scrivere su %HOSTS_FILE%.
    )
)

echo.
echo [*] Verifica / Generazione certificati SSL locali...
if not exist "%~dp0certs\server.crt" (
    python "%~dp0scripts\generate_certificates.py"
)

if exist "%~dp0certs\ca.crt" (
    echo [*] Installazione Root CA locale nel Trusted Root Certificate Store di Windows...
    certutil -addstore -f Root "%~dp0certs\ca.crt"
    if !errorlevel! equ 0 (
        echo [OK] Certificato Root CA registrato con successo.
    ) else (
        echo [!] Tentativo di importazione tramite PowerShell...
        powershell -NoProfile -Command "Import-Certificate -FilePath '%~dp0certs\ca.crt' -CertStoreLocation Cert:\LocalMachine\Root"
    )
)

echo.
echo [*] Svuotamento della cache DNS (ipconfig /flushdns)...
ipconfig /flushdns >nul
echo [OK] Cache DNS aggiornata.
echo.
echo ==============================================================================
echo   Completato con successo!
echo   IMPORTANTE: Chiudi e riapri il browser (oppure apri una nuova finestra)
echo   per fargli recepire la nuova autorita' radice attendibile.
echo   Poi naviga su: https://phdprof.test/
echo ==============================================================================
echo.
pause
