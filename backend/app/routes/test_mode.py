"""
Endpoint para gestionar modo de pruebas
Permite cargar datos desde CSV y trabajar sin afectar datos reales
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderItem, Customer, User, AuditLog
from app.services.csv_importer import import_backorders_from_csv
from werkzeug.utils import secure_filename
import os
import tempfile

bp = Blueprint('test_mode', __name__)

def is_test_mode():
    """Verifica si la petición está en modo de pruebas"""
    return request.headers.get('X-Test-Mode', '').lower() == 'true'

def get_schema_prefix():
    """Retorna el prefijo de tabla según el modo"""
    return 'test_' if is_test_mode() else ''

@bp.route('/status', methods=['GET'])
@jwt_required()
def test_status():
    """Verifica el estado del modo de pruebas"""
    test_mode = is_test_mode()
    
    if test_mode:
        # Contar registros en modo prueba
        test_orders = Order.query.filter(Order.order_number.like('TEST-%')).count()
        return jsonify({
            'test_mode': True,
            'test_orders': test_orders,
            'message': 'Modo de pruebas activo'
        })
    else:
        return jsonify({
            'test_mode': False,
            'message': 'Modo producción activo'
        })

@bp.route('/init', methods=['POST'])
@jwt_required()
def init_test_data():
    """
    Inicializa datos de prueba desde CSV sample
    POST /api/test/init
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    if not is_test_mode():
        return jsonify({'error': 'Esta operación solo está disponible en modo de pruebas'}), 400
    
    try:
        # Buscar archivo CSV de ejemplo
        csv_path = os.path.join('/app', 'Samples', 'BO_Sample.csv')
        
        print(f"[TEST_MODE] Buscando CSV en: {csv_path}")
        print(f"[TEST_MODE] CSV existe: {os.path.exists(csv_path)}")
        
        if not os.path.exists(csv_path):
            return jsonify({'error': f'Archivo CSV de ejemplo no encontrado en: {csv_path}'}), 404
        
        # Limpiar datos de prueba existentes (primero items, luego órdenes)
        subq = db.session.query(Order.id).filter(
            Order.order_number.like('TEST-%')
        ).subquery()
        deleted_items = OrderItem.query.filter(
            OrderItem.order_id.in_(subq)
        ).delete(synchronize_session=False)
        deleted_orders = Order.query.filter(Order.order_number.like('TEST-%')).delete(synchronize_session=False)
        print(f"[TEST_MODE] Ítems eliminados: {deleted_items} | Órdenes eliminadas: {deleted_orders}")
        db.session.commit()
        
        # Importar datos del CSV con prefijo TEST-
        print(f"[TEST_MODE] Iniciando importación con test_mode=True")
        result = import_backorders_from_csv(csv_path, user_id=int(user_id), test_mode=True)
        print(f"[TEST_MODE] Resultado de importación: {result}")
        
        # Registrar en auditoría
        audit = AuditLog(
            user_id=int(user_id),
            action='test_init',
            entity='test_data',
            entity_id=None,
            details={
                'deleted_orders': deleted_orders,
                'deleted_items': deleted_items,
                'new_orders': result.get('new_orders', 0),
                'updated_orders': result.get('updated_orders', 0),
                'csv_file': 'BO_Sample.csv'
            }
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'message': 'Datos de prueba inicializados correctamente',
            'new_orders': result.get('new_orders', 0),
            'updated_orders': result.get('updated_orders', 0)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"[TEST_MODE] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error inicializando datos: {str(e)}'}), 500

@bp.route('/reset', methods=['POST'])
@jwt_required()
def reset_test_data():
    """
    Elimina todos los datos de prueba y reinicia desde el CSV
    POST /api/test/reset
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    if not is_test_mode():
        return jsonify({'error': 'Esta operación solo está disponible en modo de pruebas'}), 400
    
    try:
        # Eliminar todos los datos de prueba (primero items, luego órdenes)
        subq = db.session.query(Order.id).filter(
            Order.order_number.like('TEST-%')
        ).subquery()
        deleted_items = OrderItem.query.filter(
            OrderItem.order_id.in_(subq)
        ).delete(synchronize_session=False)
        deleted_orders = Order.query.filter(Order.order_number.like('TEST-%')).delete(synchronize_session=False)
        db.session.commit()
        
        # Reinicializar desde CSV
        csv_path = os.path.join('/app', 'Samples', 'BO_Sample.csv')
        
        if os.path.exists(csv_path):
            result = import_backorders_from_csv(csv_path, test_mode=True)
        else:
            result = {'new_orders': 0, 'updated_orders': 0}
        
        # Registrar en auditoría
        audit = AuditLog(
            user_id=int(user_id),
            action='test_reset',
            entity='test_data',
            entity_id=None,
            details={
                'deleted_orders': deleted_orders,
                'deleted_items': deleted_items,
                'new_orders': result.get('new_orders', 0)
            }
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'message': 'Datos de prueba reseteados correctamente',
            'deleted_orders': deleted_orders,
            'new_orders': result.get('new_orders', 0)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error reseteando datos: {str(e)}'}), 500

@bp.route('/clear', methods=['POST'])
@jwt_required()
def clear_test_data():
    """
    Elimina todos los datos de prueba sin reinicializar
    POST /api/test/clear
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    if not is_test_mode():
        return jsonify({'error': 'Esta operación solo está disponible en modo de pruebas'}), 400
    
    try:
        # Eliminar todos los datos de prueba
        subq = db.session.query(Order.id).filter(Order.order_number.like('TEST-%')).subquery()
        deleted_items = OrderItem.query.filter(OrderItem.order_id.in_(subq)).delete(synchronize_session=False)
        deleted_orders = Order.query.filter(Order.id.in_(subq)).delete(synchronize_session=False)
        db.session.commit()
        
        # Registrar en auditoría
        audit = AuditLog(
            user_id=user_id,
            action='test_clear',
            entity='test_data',
            entity_id=None,
            details={
                'deleted_orders': deleted_orders,
                'deleted_items': deleted_items
            }
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'message': 'Datos de prueba eliminados correctamente',
            'deleted_orders': deleted_orders,
            'deleted_items': deleted_items
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error eliminando datos: {str(e)}'}), 500
