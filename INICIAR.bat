@echo off

REM ============================================================

REM Launcher para Script de Inicialización - Backorder PCM

REM Sistema de Gestión de Backorder (v2.1 - Con Modo Pruebas)

REM ============================================================



setlocal enabledelayedexpansion



echo.

echo ============================================================

echo   Inicializando Backorder PCM - Sistema de Gestión

echo ============================================================

echo.

echo   Versión: 2.2 - Soporte Extendido CSV

echo   Características:

echo   - Autenticación JWT con roles de usuario

echo   - Auditoría en tiempo real

echo   - Importación Avanzada CSV (OT, Specs, Vendedores)

echo   - Filtrado por IP

echo   - Edición en tiempo real

echo   - MODO PRUEBAS para testing sin afectar datos reales

echo.



REM Verificar si PowerShell está disponible

where powershell >nul 2>nul

if %ERRORLEVEL% NEQ 0 (

    echo ERROR: PowerShell no está disponible

    echo Por favor, instala PowerShell

    pause

    exit /b 1

)



REM Verificar si Docker está disponible

where docker >nul 2>nul

if %ERRORLEVEL% NEQ 0 (

    echo ERROR: Docker no está disponible

    echo Por favor, instala Docker Desktop

    pause

    exit /b 1

)



echo Iniciando contenedores Docker...

echo.



REM Ejecutar script de PowerShell con política de ejecución bypass

set MODE=dev

set /p MODE=Selecciona modo (dev/prod) [dev]: 

if "%MODE%"=="" set MODE=dev

if /I "%MODE%"=="prod" (

    set PS_ARGS=

) else (

    set PS_ARGS=-Dev

)




powershell.exe -ExecutionPolicy Bypass -File "%~dp0iniciar.ps1" %PS_ARGS%



pause

