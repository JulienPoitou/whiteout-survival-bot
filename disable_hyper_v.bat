@echo off
echo ================================================
echo   Disable Hyper-V for LDPlayer Performance
echo ================================================
echo.
echo This will disable Hyper-V and related features
echo that slow down Android emulators.
echo.
echo WARNING: This requires a RESTART to take effect!
echo.
pause

echo.
echo Disabling Hyper-V...
powershell -Command "Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart"

echo.
echo Disabling Windows Sandbox...
powershell -Command "Disable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -NoRestart"

echo.
echo Disabling Virtual Machine Platform...
powershell -Command "Disable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart"

echo.
echo Disabling Windows Hypervisor Platform...
powershell -Command "Disable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -NoRestart"

echo.
echo Disabling Windows Subsystem for Linux...
powershell -Command "Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart"

echo.
echo ================================================
echo   DONE!
echo ================================================
echo.
echo All Hyper-V features have been disabled.
echo.
echo *** YOU MUST RESTART YOUR COMPUTER ***
echo.
echo After restart, LDPlayer will have MUCH better performance!
echo.
echo Do you want to restart NOW? (Y/N)
set /p restart="> "
if /i "%restart%"=="Y" (
    echo.
    echo Restarting in 5 seconds...
    timeout /t 5
    shutdown /r /t 0
) else (
    echo.
    echo Please restart your computer manually when ready.
    pause
)
