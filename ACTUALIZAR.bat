@echo off
REM ============================================================
REM Script de Actualización Rápida - Backorder PCM v2.2
REM Reconstruye y reinicia los contenedores con última versión
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo   Actualización Rápida - Backorder PCM v2.2
echo ============================================================
echo.
echo   Este script reconstruirá los contenedores con
echo   la versión más reciente del código.
echo.

REM Verificar Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker no está disponible
    pause
    exit /b 1
)

REM Mostrar opciones
echo Opciones de actualización:
echo.
echo  1 = Actualización completa (reconstruir todo)
echo  2 = Actualización frontend solo
echo  3 = Actualización backend solo
echo  4 = Actualización sin reconstruir (pull de imágenes)
echo.

set /p option="Elige una opción (1-4): "

if "%option%"=="1" (
    echo.
    echo [INFO] Deteniendo sistema...
    docker-compose down
    
    echo.
    echo [INFO] Reconstruyendo todas las imágenes...
    docker-compose up -d --build
    
    goto :success
)

if "%option%"=="2" (
    echo.
    echo [INFO] Compilando frontend...
    cd frontend
    call npm run build
    cd ..
    
    echo.
    echo [INFO] Reconstruyendo contenedor frontend...
    docker-compose up -d --build frontend
    
    goto :success
)

if "%option%"=="3" (
    echo.
    echo [INFO] Reconstruyendo contenedor backend...
    docker-compose up -d --build backend
    
    goto :success
)

if "%option%"=="4" (
    echo.
    echo [INFO] Actualizando imágenes de repositorio...
    docker-compose pull
    
    echo.
    echo [INFO] Reiniciando contenedores...
    docker-compose restart
    
    goto :success
)

echo.
echo [ERROR] Opción no válida
echo.
pause
exit /b 1

:success
echo.
echo ============================================================
echo   Actualización Completada
echo ============================================================
echo.
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:5000/health
echo.
echo [INFO] Espera 10 segundos mientras los servicios inician...
timeout /t 10 /nobreak
echo.
echo [OK] Sistema actualizado y reiniciado
echo.
pause
