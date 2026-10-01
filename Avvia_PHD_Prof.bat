@echo off
:: Launches PHD Prof Web Cockpit silently via Windows Script Host
cd /d "%~dp0"
start "" wscript.exe "%~dp0Avvia_PHD_Prof.vbs"
exit
