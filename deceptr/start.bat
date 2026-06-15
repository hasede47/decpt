@echo off
title DECEPTR v1 - Architecture T-Pot
color 0A

echo.
echo  DECEPTR v1 - Architecture cible
echo  Cowrie officiel T-Pot -^> DECEPTR Logstash TLS -^> Pipeline -^> Dashboards
echo  ---------------------------------------------------------------
echo.

docker info >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo  [ERREUR] Docker Desktop n'est pas demarre ou son moteur Linux est bloque.
    echo  Ouvre Docker Desktop, attends "Engine running", puis relance start.bat.
    pause
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start-architecture.ps1"
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo  [ERREUR] Echec du demarrage architecture.
    pause
    exit /b 1
)

echo.
echo  ---------------------------------------------------------------
echo  [OK] DECEPTR est actif en mode architecture.
echo.
echo  Dashboard DECEPTR : http://127.0.0.1:8088/index.html?v=3
echo  API Docs          : http://127.0.0.1:8000/docs
echo  Kibana DECEPTR    : http://127.0.0.1:5601
echo.
echo  Login API         : admin / deceptr2025
echo.
echo  Honeypot T-Pot Cowrie:
echo    SSH             : ssh root@127.0.0.1 -p 22
echo    Telnet          : telnet 127.0.0.1 23
echo  ---------------------------------------------------------------
echo.
pause
