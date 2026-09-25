@echo off
title PHD Prof - Document ETL to Notion
cd /d "%~dp0"

echo ==========================================================
echo   AVVIO PHD PROF...
echo ==========================================================
echo.

"C:\Users\3003f\AppData\Local\Programs\Python\Python311\python.exe" pdf_to_notion.py

echo.
echo ==========================================================
echo   Sessione conclusa.
echo ==========================================================
pause
