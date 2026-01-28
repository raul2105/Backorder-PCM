@echo off
REM ============================================================
REM Verificación de Salud - Backorder PCM
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ============================================================
echo   Verificación de Salud del Sistema - Backorder PCM v2.1
echo ============================================================
echo.

REM Variables
set "API_URL=http://localhost:5000"
set "FRONTEND_URL=http://localhost:3000"
set "DB_HOST=localhost"
set "DB_PORT=5432"

echo [VERIFICANDO] Estado de Contenedores Docker...
echo.

REM Verificar Docker
where docker >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker no está instalado
    echo Por favor, instala Docker Desktop
    pause
    exit /b 1
)

REM Listar contenedores
docker-compose ps

echo.
echo [VERIFICANDO] Conectividad de Servicios...
echo.

REM Verificar Backend
echo Probando Backend API (%API_URL%)...
curl -s %API_URL%/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Backend respondiendo
) else (
    echo [ERROR] Backend no responde
)

REM Verificar Frontend
echo Probando Frontend (%FRONTEND_URL%)...
curl -s %FRONTEND_URL% >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Frontend disponible
) else (
    echo [ERROR] Frontend no responde
)

REM Verificar Puerto 5432 (PostgreSQL)
netstat -an | findstr :5432 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] PostgreSQL escuchando en puerto 5432
) else (
    echo [WARN] PostgreSQL no detectado en puerto 5432
)

REM Verificar Puerto 6379 (Redis)
netstat -an | findstr :6379 >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Redis escuchando en puerto 6379
) else (
    echo [WARN] Redis no detectado en puerto 6379
)

echo.
echo ============================================================
echo   Resumen de Puertos
echo ============================================================
echo.
echo   Frontend:    http://localhost:3000
echo   Backend API: http://localhost:5000
echo   PostgreSQL:  localhost:5432
echo   Redis:       localhost:6379
echo.

REM Ver logs recientes
echo.
echo [INFO] Últimos eventos de Docker:
echo.
docker-compose logs --tail=10

echo.
echo ============================================================
echo.
pause
