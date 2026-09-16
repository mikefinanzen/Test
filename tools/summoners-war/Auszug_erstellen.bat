@echo off
setlocal
title SWEX-Auszug erstellen
echo.
echo   Summoners War - Box-Auszug wird erstellt ...
echo.

set "PY="
where python >/dev/null 2>&1 && set "PY=python"
if not defined PY ( where py >/dev/null 2>&1 && set "PY=py -3" )
if not defined PY (
  echo   Python ist nicht installiert.
  echo   Bitte von https://www.python.org/downloads/ installieren
  echo   und dabei "Add python.exe to PATH" ankreuzen.
  echo.
  pause
  exit /b 1
)

%PY% "%~dp0sw_export_summary.py" --auto --clip -o "%~dp0auszug.txt"

echo.
pause
