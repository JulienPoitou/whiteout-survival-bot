@echo off
echo.
echo ================================================
echo   TEMPLATE HUNTER - AUTO 10min RESTART
echo ================================================
echo.
echo Ce script va:
echo   1. Lancer le Template Hunter
echo   2. Faire un rapport toutes les 10 minutes
echo   3. Redémarrer automatiquement
echo   4. Tourner jusqu'à arrêt manuel (Ctrl+C)
echo.
echo Pour arreter: Ctrl+C
echo ================================================
echo.

cd /d "%~dp0"

:loop
python hunter_launcher.py
goto loop

pause
