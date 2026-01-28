@echo off
REM ============================================================
REM Detener Sistema Backorder PCM - v2.2
REM Sistema de Gestión de Backorder con Modo Pruebas
REM ============================================================

echo.
echo ============================================================
echo   Deteniendo Backorder PCM v2.2
echo ============================================================
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0detener.ps1"

pause
