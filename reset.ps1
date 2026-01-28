# ============================================================
# Script de Reset Completo - Backorder PCM
# ============================================================
# ADVERTENCIA: Este script eliminará TODOS los datos
# ============================================================

Write-Host "============================================================" -ForegroundColor Red
Write-Host "  RESET COMPLETO - Backorder PCM" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Red
Write-Host ""
Write-Host "ADVERTENCIA: Esta acción eliminará:" -ForegroundColor Yellow
Write-Host "  - Todos los contenedores" -ForegroundColor Gray
Write-Host "  - Toda la base de datos" -ForegroundColor Gray
Write-Host "  - Todos los volúmenes de datos" -ForegroundColor Gray
Write-Host "  - Todas las configuraciones" -ForegroundColor Gray
Write-Host ""

$confirm1 = Read-Host "¿Estás seguro de que deseas continuar? (escribe SI para confirmar)"

if ($confirm1 -ne "SI") {
    Write-Host ""
    Write-Host "Reset cancelado" -ForegroundColor Green
    Write-Host ""
    Read-Host "Presiona Enter para cerrar"
    exit
}

Write-Host ""
$confirm2 = Read-Host "Última confirmación - ¿Eliminar TODOS los datos? (escribe ELIMINAR para confirmar)"

if ($confirm2 -ne "ELIMINAR") {
    Write-Host ""
    Write-Host "Reset cancelado" -ForegroundColor Green
    Write-Host ""
    Read-Host "Presiona Enter para cerrar"
    exit
}

Write-Host ""
Write-Host "[INFO] Deteniendo servicios..." -ForegroundColor Yellow
docker-compose down

Write-Host "[INFO] Eliminando volúmenes..." -ForegroundColor Yellow
docker-compose down -v

Write-Host "[INFO] Limpiando imágenes no utilizadas..." -ForegroundColor Yellow
docker image prune -f

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Reset Completado" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "El sistema ha sido completamente eliminado." -ForegroundColor Gray
Write-Host ""
Write-Host "Para iniciar nuevamente desde cero, ejecuta: " -NoNewline
Write-Host ".\iniciar.ps1" -ForegroundColor Cyan
Write-Host ""

Read-Host "Presiona Enter para cerrar"
