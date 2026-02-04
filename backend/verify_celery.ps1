# Script PowerShell para verificar la configuración de Celery

Write-Host "🔍 Verificando configuración de Celery..." -ForegroundColor Cyan
Write-Host ""

# Verificar que celery_app.py existe
if (Test-Path "celery_app.py") {
    Write-Host "✅ celery_app.py encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ celery_app.py NO encontrado" -ForegroundColor Red
    exit 1
}

# Verificar que la aplicación puede importar correctamente
Write-Host ""
Write-Host "🐍 Verificando imports de Python..." -ForegroundColor Cyan

$pythonCode = @"
try:
    from celery_app import celery, flask_app
    print('✅ celery_app importado correctamente')
    print(f'   - Broker: {celery.conf.broker_url}')
    print(f'   - Backend: {celery.conf.result_backend}')
    
    from app.services.sync_service import sync_all_erps
    print(f'✅ Task sync_all_erps importada: {sync_all_erps.name}')
except Exception as e:
    print(f'❌ Error en imports: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"@

python -c $pythonCode

if ($LASTEXITCODE -ne 0) {
    exit 1
}

Write-Host ""
Write-Host "✅ Verificación completada" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Para iniciar los servicios:" -ForegroundColor Yellow
Write-Host "   docker-compose up -d celery_worker celery_beat"
Write-Host ""
Write-Host "📝 Para ver logs del worker:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f celery_worker"
Write-Host ""
Write-Host "📝 Para disparar tarea manualmente desde Flask:" -ForegroundColor Yellow
Write-Host "   docker-compose exec backend flask test-celery"
