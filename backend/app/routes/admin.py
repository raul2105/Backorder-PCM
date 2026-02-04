"""
Rutas de administración (solo para usuarios con rol admin)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import db
from app.models import User, AuditLog
from app.utils.auth_helpers import get_current_user, get_current_user_id
from app.models import User, AuditLog, Order, OrderItem, ProductionLog
from app.middleware import require_allowed_ip, ROLE_OPTIONS

bp = Blueprint('admin', __name__)


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin':
            return jsonify({'error': 'No autorizado'}), 403
        return f(*args, **kwargs)
    return wrapper


@bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'is_active': u.is_active,
            'last_login': u.last_login.isoformat() if u.last_login else None,
        } for u in users
    ])


@bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required
@require_allowed_ip
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'planning')

    if not username or not email or not password:
        return jsonify({'error': 'Datos incompletos'}), 400

    if role not in ROLE_OPTIONS:
        return jsonify({'error': 'Rol invÃ¡lido'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Usuario ya existe'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email ya registrado'}), 400

    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(new_user)
    db.session.commit()

    current_user_id = get_current_user_id()
    if current_user_id:
        db.session.add(AuditLog(user_id=current_user_id, action='create_user', entity='user', entity_id=str(new_user.id), details={'username': username, 'role': role}))
        db.session.commit()

    return jsonify({'message': 'Usuario creado', 'id': new_user.id}), 201


@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
@require_allowed_ip
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    changes = {}

    if 'role' in data:
        if data['role'] not in ROLE_OPTIONS:
            return jsonify({'error': 'Rol invÃ¡lido'}), 400
        changes['role'] = {'old': user.role, 'new': data['role']}
        user.role = data['role']
    if 'is_active' in data:
        changes['is_active'] = {'old': user.is_active, 'new': data['is_active']}
        user.is_active = bool(data['is_active'])
    if 'password' in data and data['password']:
        changes['password'] = 'updated'
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()

    current_user_id = get_current_user_id()
    if current_user_id:
        db.session.add(AuditLog(user_id=current_user_id, action='update_user', entity='user', entity_id=str(user.id), details=changes))
        db.session.commit()

    return jsonify({'message': 'Usuario actualizado'})


@bp.route('/audit', methods=['GET'])
@jwt_required()
@admin_required
def list_audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all()
    return jsonify([
        {
            'id': l.id,
            'user_id': l.user_id,
            'action': l.action,
            'entity': l.entity,
            'entity_id': l.entity_id,
            'details': l.details,
            'created_at': l.created_at.isoformat(),
        } for l in logs
    ])


@bp.route('/tasks/sync-erps', methods=['POST'])
@jwt_required()
@admin_required
@require_allowed_ip
def trigger_sync_task():
    """Disparar manualmente la tarea de sincronización de ERPs"""
    try:
        # Importar la tarea desde celery_app para tener la configuración correcta
        from app.services.sync_service import sync_all_erps
        
        # Disparar la tarea de forma asíncrona
        task = sync_all_erps.apply_async()
        
        # Registrar en audit log
        db.session.add(AuditLog(
            user_id=int(get_jwt_identity()),
            action='trigger_sync_task',
            entity='celery_task',
            entity_id=task.id,
            details={'task_name': 'sync_all_erps'}
        ))
        db.session.commit()
        
        return jsonify({
            'message': 'Tarea de sincronización iniciada',
            'task_id': task.id,
            'status': 'PENDING'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al disparar tarea: {str(e)}'}), 500


@bp.route('/tasks/<task_id>/status', methods=['GET'])
@jwt_required()
@admin_required
def get_task_status(task_id):
    """Consultar el estado de una tarea de Celery"""
    try:
        from celery.result import AsyncResult
        from celery_app import celery
        
        task = AsyncResult(task_id, app=celery)
        
        response = {
            'task_id': task_id,
            'status': task.state,
            'result': None
        }
        
        if task.state == 'SUCCESS':
            response['result'] = task.result
        elif task.state == 'FAILURE':
            response['error'] = str(task.info)
        elif task.state == 'PENDING':
            response['message'] = 'Tarea en cola o no encontrada'
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al consultar estado: {str(e)}'}), 500


@bp.route('/erp/circuit-breakers', methods=['GET'])
@jwt_required()
@admin_required
def get_circuit_breaker_status():
    """Consultar el estado de los circuit breakers de cada ERP"""
    try:
        from app.erp_connectors import ERPConnectorFactory
        
        connectors = ERPConnectorFactory.get_all_active_connectors()
        
        statuses = []
        for connector_info in connectors:
            connector = connector_info['connector']
            status = connector.get_circuit_breaker_status()
            statuses.append(status)
        
        return jsonify({
            'circuit_breakers': statuses,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al consultar circuit breakers: {str(e)}'}), 500


@bp.route('/purge/orders', methods=['POST'])
@jwt_required()
@admin_required
@require_allowed_ip
def purge_orders_by_date():
    """Depurar Ã³rdenes por fecha sin afectar ERPs (solo elimina datos locales)"""
    data = request.get_json() or {}
    before_date = data.get('before_date')
    include_erp = bool(data.get('include_erp', False))
    dry_run = bool(data.get('dry_run', True))

    if not before_date:
        return jsonify({'error': 'before_date es requerido (YYYY-MM-DD)'}), 400

    try:
        cutoff = datetime.strptime(before_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Formato de before_date invÃ¡lido, usa YYYY-MM-DD'}), 400

    orders_query = Order.query.filter(Order.order_date <= cutoff)
    if not include_erp:
        orders_query = orders_query.filter(Order.erp_source.is_(None))

    order_ids = [o.id for o in orders_query.all()]
    if not order_ids:
        return jsonify({
            'message': 'No hay Ã³rdenes para depurar',
            'orders_deleted': 0,
            'items_deleted': 0,
            'production_logs_deleted': 0,
            'dry_run': dry_run,
        }), 200

    items_count = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).count()
    logs_count = ProductionLog.query.filter(ProductionLog.order_id.in_(order_ids)).count()

    if dry_run:
        return jsonify({
            'message': 'PrevisualizaciÃ³n de depuraciÃ³n',
            'orders_to_delete': len(order_ids),
            'items_to_delete': items_count,
            'production_logs_to_delete': logs_count,
            'dry_run': True,
            'include_erp': include_erp,
            'cutoff_date': cutoff.date().isoformat(),
        }), 200

    deleted_items = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
    deleted_logs = ProductionLog.query.filter(ProductionLog.order_id.in_(order_ids)).delete(synchronize_session=False)
    deleted_orders = Order.query.filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
    db.session.commit()

    db.session.add(AuditLog(
        user_id=int(get_jwt_identity()),
        action='purge_orders',
        entity='order',
        entity_id=str(len(order_ids)),
        details={
            'before_date': cutoff.date().isoformat(),
            'include_erp': include_erp,
            'orders_deleted': deleted_orders,
            'items_deleted': deleted_items,
            'production_logs_deleted': deleted_logs,
        }
    ))
    db.session.commit()

    return jsonify({
        'message': 'DepuraciÃ³n completada',
        'orders_deleted': deleted_orders,
        'items_deleted': deleted_items,
        'production_logs_deleted': deleted_logs,
        'dry_run': False,
        'include_erp': include_erp,
        'cutoff_date': cutoff.date().isoformat(),
    }), 200
