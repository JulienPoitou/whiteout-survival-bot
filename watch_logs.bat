@echo off
echo.
echo ================================================
echo   TEMPLATE HUNTER V3 - LOGS EN TEMPS RÉEL
echo ================================================
echo.
echo Appuie sur Ctrl+C pour arreter le suivi
echo.
powershell -Command "Get-Content logs\hunter_v3.log -Wait -Tail 30"
