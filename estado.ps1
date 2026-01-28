# ============================================================
# Script de Estado del Sistema - Backorder PCM
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Estado del Sistema - Backorder PCM" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
Write-Host "Docker Desktop: " -NoNewline
try {
    docker ps 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "CORRIENDO" -ForegroundColor Green
    }
} catch {
    Write-Host "NO DISPONIBLE" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Estado de los Servicios:" -ForegroundColor Yellow
Write-Host ""

docker-compose ps

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Información de Conexiones" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1).IPAddress

Write-Host "URLs de Acceso:" -ForegroundColor Yellow
Write-Host "  Local:     http://localhost:3000" -ForegroundColor Green
if ($localIP) {
    Write-Host "  Red:       http://${localIP}:3000" -ForegroundColor Green
}

Write-Host ""
Write-Host "Uso de Recursos:" -ForegroundColor Yellow

try {
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
} catch {
    Write-Host "No se pudo obtener estadísticas de recursos" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Volúmenes de Datos:" -ForegroundColor Yellow
docker volume ls | Select-String "backorder"

Write-Host ""
Write-Host "Para ver logs en tiempo real: " -NoNewline
Write-Host ".\ver-logs.ps1" -ForegroundColor Cyan

Write-Host ""
Read-Host "Presiona Enter para cerrar"
