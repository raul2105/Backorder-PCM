"""
Punto de entrada de la aplicación Flask
"""

import os
from app import create_app, db
from app.models import User, Order, Customer, Material, OrderItem, ProductionLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Contexto para Flask shell"""
    return {
        'db': db,
        'User': User,
        'Order': Order,
        'Customer': Customer,
        'Material': Material,
        'OrderItem': OrderItem,
        'ProductionLog': ProductionLog
    }

@app.cli.command()
def init_db():
    """Inicializar la base de datos"""
    db.create_all()
    print('Base de datos inicializada')

@app.cli.command()
def create_admin():
    """Crear usuario administrador por defecto"""
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print('Usuario admin ya existe')
        return
    
    admin = User(
        username='admin',
        email='admin@backorder.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        must_change_password=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print('Usuario admin creado exitosamente')


@app.cli.command()
def test_celery():
    """Disparar tarea de prueba de Celery"""
    print('🚀 Disparando tarea de sincronización de ERPs...')
    
    try:
        from app.services.sync_service import sync_all_erps
        task = sync_all_erps.apply_async()
        
        print(f'✅ Tarea disparada exitosamente')
        print(f'   Task ID: {task.id}')
        print(f'   Estado inicial: {task.state}')
        print(f'\n📝 Para verificar el estado:')
        print(f'   curl -X GET http://localhost:5000/api/admin/tasks/{task.id}/status \\')
        print(f'        -H "Authorization: Bearer <tu_token>"')
        
        return task.id
        
    except Exception as e:
        print(f'❌ Error al disparar tarea: {str(e)}')
        import traceback
        traceback.print_exc()


@app.cli.command()
def test_celery_sync():
    """Ejecutar sincronización de forma síncrona (sin Celery) para debug"""
    print('🔄 Ejecutando sincronización síncrona (modo debug)...')
    
    try:
        from app.services.sync_service import SyncService
        
        # Obtener conectores activos
        from app.erp_connectors import ERPConnectorFactory
        active_connectors = ERPConnectorFactory.get_all_active_connectors()
        
        print(f'📊 Conectores activos: {len(active_connectors)}')
        
        for connector_info in active_connectors:
            erp_name = connector_info['name']
            print(f'\n🔌 Sincronizando {erp_name}...')
            
            # Sincronizar órdenes
            order_result = SyncService.sync_orders_from_erp(erp_name)
            print(f'   Órdenes: {order_result}')
            
            # Sincronizar materiales
            material_result = SyncService.sync_materials_from_erp(erp_name)
            print(f'   Materiales: {material_result}')
        
        print('\n✅ Sincronización completada')
        
    except Exception as e:
        print(f'❌ Error en sincronización: {str(e)}')
        import traceback
        traceback.print_exc()
    print('Username: admin')
    print('Password: admin123')
    print('IMPORTANTE: Cambiar la contraseña en producción')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
