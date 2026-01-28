# ============================================================
# Script de Detención - Backorder PCM
# Versión 2.2 - Modo Pruebas Integrado
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Deteniendo Sistema Backorder PCM" -ForegroundColor Cyan
Write-Host "  Versión 2.2" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Función para mostrar mensajes con estilo
function Write-Step {
    param($Message)
    Write-Host "[INFO] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

Write-Step "Verificando estado de contenedores..."
$status = docker-compose ps --format json | ConvertFrom-Json
$runningCount = @($status | Where-Object { $_.State -like "*Up*" }).Count

if ($runningCount -eq 0) {
    Write-Host "[WARN] No hay contenedores en ejecución" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para iniciar el sistema, ejecuta: " -NoNewline
    Write-Host ".\iniciar.ps1" -ForegroundColor Cyan
    Read-Host "Presiona Enter para cerrar"
    exit
}

Write-Step "Deteniendo $runningCount contenedores..."
Write-Host ""

docker-compose stop

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  Sistema Detenido Correctamente" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Estado:" -ForegroundColor Cyan
    Write-Host "  • Los contenedores están detenidos pero no eliminados" -ForegroundColor Gray
    Write-Host "  • Los datos se mantienen en las bases de datos" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Próximos pasos:" -ForegroundColor Yellow
    Write-Host "  Para iniciar nuevamente:" -NoNewline
    Write-Host " .\iniciar.ps1" -ForegroundColor Cyan
    Write-Host "  Para eliminar completamente:" -NoNewline
    Write-Host " docker-compose down" -ForegroundColor Yellow
    Write-Host "  Para ver logs históricos:" -NoNewline
    Write-Host " docker-compose logs" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[ERROR] Error al detener los servicios" -ForegroundColor Red
    Write-Host "Por favor, intenta manualmente con: docker-compose stop" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Presiona Enter para cerrar"
