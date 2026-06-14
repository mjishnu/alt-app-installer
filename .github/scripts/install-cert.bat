@echo off
setlocal

set "CERT_FILE=%~dp0altappinstaller.cer"

if not exist "%CERT_FILE%" (
    echo Certificate file not found: "%CERT_FILE%"
    pause
    exit /b 1
)

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

certutil -addstore -f Root "%CERT_FILE%" >nul
if %errorlevel% neq 0 (
    echo Failed to install certificate into Trusted Root Certification Authorities.
    pause
    exit /b 1
)

echo Certificate installed successfully to Trusted Root Certification Authorities (Local Machine).
pause
exit /b 0
