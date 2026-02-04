#!/bin/bash
# Script para verificar la configuración de Celery

echo "🔍 Verificando configuración de Celery..."
echo ""

# Verificar que celery_app.py existe
if [ -f "celery_app.py" ]; then
    echo "✅ celery_app.py encontrado"
else
    echo "❌ celery_app.py NO encontrado"
    exit 1
fi

# Listar las tareas registradas
echo ""
echo "📋 Listando tareas registradas:"
celery -A celery_app.celery inspect registered 2>/dev/null || {
    echo "⚠️  No se pudo conectar al worker (puede ser normal si no está corriendo)"
}

# Verificar que la aplicación puede importar correctamente
echo ""
echo "🐍 Verificando imports de Python..."
python -c "
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
" || exit 1

echo ""
echo "✅ Verificación completada"
echo ""
echo "📝 Para iniciar los servicios:"
echo "   docker-compose up -d celery_worker celery_beat"
echo ""
echo "📝 Para ver logs del worker:"
echo "   docker-compose logs -f celery_worker"
echo ""
echo "📝 Para disparar tarea manualmente desde Flask:"
echo "   docker-compose exec backend flask test-celery"
