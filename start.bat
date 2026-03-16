@echo off
echo ===============================================
echo   Whiteout Survival - Autonomous Bot
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python n'est pas installe !
    echo Telecharge-le sur: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python installe
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama ne semble pas tourner...
    echo Lance 'ollama serve' dans un autre terminal
    echo.
    echo Vouloir continuer quand meme ? (Y/N)
    set /p continue="> "
    if /i not "%continue%"=="Y" exit /b 1
    echo.
) else (
    echo [OK] Ollama tourne
)

echo.
echo ===============================================
echo   Lancement du bot autonome...
echo ===============================================
echo.
echo Le bot va:
echo   1. Se connecter a LDPlayer
echo   2. Explorer l'interface
echo   3. Apprendre tout seul
echo   4. Devenir plus intelligent avec le temps
echo.
echo Pour arreter: Ctrl+C
echo ===============================================
echo.

python autonomous_bot.py

pause
