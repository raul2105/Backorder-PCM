# ============================================================
# Script de Logs en Tiempo Real - Backorder PCM
# ============================================================

param(
    [string]$Service = ""
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Visualización de Logs - Backorder PCM" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($Service) {
    Write-Host "Mostrando logs de: " -NoNewline
    Write-Host $Service -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para salir" -ForegroundColor Gray
    Write-Host ""
    docker-compose logs -f $Service
} else {
    Write-Host "Mostrando logs de todos los servicios" -ForegroundColor Yellow
    Write-Host "Presiona Ctrl+C para salir" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Servicios disponibles para ver individualmente:" -ForegroundColor Cyan
    Write-Host "  .\ver-logs.ps1 backend" -ForegroundColor Gray
    Write-Host "  .\ver-logs.ps1 frontend" -ForegroundColor Gray
    Write-Host "  .\ver-logs.ps1 db" -ForegroundColor Gray
    Write-Host "  .\ver-logs.ps1 redis" -ForegroundColor Gray
    Write-Host "  .\ver-logs.ps1 celery_worker" -ForegroundColor Gray
    Write-Host ""
    docker-compose logs -f
}
