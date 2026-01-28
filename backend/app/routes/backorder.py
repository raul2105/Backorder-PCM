"""
Rutas de Backorder - Gestión principal
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Order, OrderItem, Customer, AuditLog, SystemSetting
from datetime import datetime
from sqlalchemy import or_, and_
import ipaddress

bp = Blueprint('backorder', __name__)


def _ip_allowed(ip: str) -> bool:
    """Valida si la IP del cliente está permitida para operaciones de escritura.
    Si no hay configuración, permite por defecto.
    """
    setting = SystemSetting.query.filter_by(key='network.allowed_ips').first()
    if not setting or not setting.value:
        return True
    allowed = setting.value
    try:
        for rule in allowed:
            rule = rule.strip()
            if not rule:
                continue
            # Coincidencia directa
            if rule == ip:
                return True
            # CIDR
            try:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(rule, strict=False):
                    return True
            except ValueError:
                continue
    except Exception:
        # Ante cualquier problema con la configuración, permitir para no bloquear
        return True
    return False


@bp.route('', methods=['GET'])
@jwt_required()
def get_backorders():
    """Obtener lista de backorders"""
    # Parámetros de filtrado
    status = request.args.get('status')
    customer_id = request.args.get('customer_id')
    priority = request.args.get('priority')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search = request.args.get('search')
    
    query = Order.query.filter_by(is_backorder=True)
    
    # Aplicar filtros
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Order.order_number.ilike(search_term),
            Order.customer_name.ilike(search_term)
        ))
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if priority:
        query = query.filter(Order.priority == int(priority))
    if date_from:
        query = query.filter(Order.order_date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Order.order_date <= datetime.fromisoformat(date_to))
    
    # Ordenar por prioridad y fecha prometida
    orders = query.order_by(Order.priority.asc(), Order.promised_date.asc()).all()
    
    return jsonify({
        'total': len(orders),
        'backorders': [order.to_dict() for order in orders]
    }), 200


@bp.route('', methods=['POST'])
@jwt_required()
def create_backorder():
    """Crear nueva orden manualmente"""
    data = request.get_json()
    
    # Validaciones básicas
    if not data.get('order_number'):
        return jsonify({'error': 'El número de orden es requerido'}), 400
    if not data.get('customer_code'):
        return jsonify({'error': 'El código de cliente es requerido'}), 400
        
    # Verificar existencia
    if Order.query.filter_by(order_number=data['order_number']).first():
        return jsonify({'error': 'El número de orden ya existe'}), 400
        
    try:
        # 1. Gestionar Cliente
        customer = Customer.query.filter_by(customer_code=data['customer_code']).first()
        if not customer:
            customer = Customer(
                customer_code=data['customer_code'],
                name=data.get('customer_name', data['customer_code']),
                erp_source='manual',
                erp_id=f"MANUAL-{data['customer_code']}"
            )
            db.session.add(customer)
            db.session.flush()
            
        # 2. Crear Orden
        new_order = Order(
            order_number=data['order_number'],
            customer_id=customer.id,
            customer_name=customer.name,
            order_date=datetime.utcnow(), # Hoy
            promised_date=datetime.fromisoformat(data['promised_date']) if data.get('promised_date') else None,
            status='pending',
            priority=int(data.get('priority', 3)),
            is_backorder=True, # Por defecto es backorder si se crea manual
            backorder_reason=data.get('backorder_reason', 'Ingreso Manual'),
            sales_rep=data.get('sales_rep'),
            # Estados iniciales
            planning_status='pending',
            warehouse_status='pending',
            purchasing_status='pending',
            production_status='pending',
            logistics_status='pending',
            erp_source='manual'
        )
        db.session.add(new_order)
        db.session.flush()
        
        # 3. Items
        items_data = data.get('items', [])
        for item in items_data:
            if not item.get('item_code') or not item.get('quantity'):
                continue
                
            new_item = OrderItem(
                order_id=new_order.id,
                item_code=item['item_code'],
                item_description=item.get('description', ''),
                quantity_ordered=float(item['quantity']),
                unit=item.get('unit', 'PZA'),
                work_order=item.get('work_order'),
                specifications=item.get('specifications', {}) # Espera dict
            )
            db.session.add(new_item)
            
        db.session.commit()
        
        return jsonify({
            'message': 'Orden creada exitosamente',
            'order': new_order.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_backorder_detail(order_id):
    """Obtener detalle de un backorder"""
    order = Order.query.get_or_404(order_id)
    
    items = OrderItem.query.filter_by(order_id=order_id).all()
    
    return jsonify({
        'order': order.to_dict(),
        'items': [{
            'id': item.id,
            'item_code': item.item_code,
            'description': item.item_description,
            'quantity_ordered': item.quantity_ordered,
            'quantity_produced': item.quantity_produced,
            'quantity_shipped': item.quantity_shipped,
            'unit': item.unit,
            'status': item.status,
            'work_order': item.work_order,
            'specifications': item.specifications
        } for item in items]
    }), 200

@bp.route('/<int:order_id>/department-status', methods=['PUT'])
@jwt_required()
def update_department_status(order_id):
    """Actualizar estado departamental de una orden"""
    order = Order.query.get_or_404(order_id)
    data = request.json
    
    department = data.get('department') # planning_status, etc.
    status = data.get('status')
    
    valid_departments = [
        'planning_status', 'warehouse_status', 'purchasing_status', 
        'production_status', 'logistics_status'
    ]
    
    if department not in valid_departments:
         return jsonify({'error': 'Departamento inválido'}), 400

    # Actualizar estado dinámicamente
    setattr(order, department, status)
    
    # Lógica de sincronización de estados (opcional)
    # Si producción se completa, marcar items como producidos? (Depende de reglas de negocio)
    
    db.session.commit()
    
    # Audit Log
    user_id = get_jwt_identity().get('id')
    log = AuditLog(
        user_id=user_id,
        action='update_dept_status',
        entity='order',
        entity_id=str(order.id),
        details={'department': department, 'new_status': status}
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'order': order.to_dict()}), 200


@bp.route('/<int:order_id>/priority', methods=['PUT'])
@jwt_required()
def update_priority(order_id):
    """Actualizar prioridad de un backorder"""
    order = Order.query.get_or_404(order_id)
    
    data = request.get_json()
    new_priority = data.get('priority')
    
    if not new_priority or new_priority not in [1, 2, 3, 4]:
        return jsonify({'error': 'Prioridad inválida (1-4)'}), 400
    # Validar IP
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    if not _ip_allowed(client_ip):
        return jsonify({'error': 'Operación no permitida desde esta IP'}), 403
    
    old_priority = order.priority
    order.priority = new_priority
    order.updated_at = datetime.utcnow()
    
    db.session.commit()
    # Auditoría
    db.session.add(AuditLog(
        user_id=int(get_jwt_identity()),
        action='update_priority',
        entity='order',
        entity_id=str(order.id),
        details={'old': old_priority, 'new': new_priority}
    ))
    db.session.commit()
    
    return jsonify({
        'message': 'Prioridad actualizada',
        'order': order.to_dict()
    }), 200


@bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_status(order_id):
    """Actualizar estado de un backorder"""
    order = Order.query.get_or_404(order_id)
    
    data = request.get_json()
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'in_production', 'ready', 'shipped', 'delivered']
    
    if not new_status or new_status not in valid_statuses:
        return jsonify({'error': f'Estado inválido. Debe ser: {", ".join(valid_statuses)}'}), 400
    
    # Validar IP
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    if not _ip_allowed(client_ip):
        return jsonify({'error': 'Operación no permitida desde esta IP'}), 403

    old_status = order.status
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    # Si se marca como completado, quitar de backorder
    if new_status in ['delivered']:
        order.is_backorder = False
    
    db.session.commit()
    # Auditoría
    db.session.add(AuditLog(
        user_id=int(get_jwt_identity()),
        action='update_status',
        entity='order',
        entity_id=str(order.id),
        details={'old': old_status, 'new': new_status}
    ))
    db.session.commit()
    
    return jsonify({
        'message': 'Estado actualizado',
        'order': order.to_dict()
    }), 200


@bp.route('/<int:order_id>/items/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_order_item(order_id, item_id):
    """Actualizar cantidad producida/enviada de un item"""
    from app.models import OrderItem
    item = OrderItem.query.get_or_404(item_id)
    if item.order_id != order_id:
        return jsonify({'error': 'Item no pertenece a esta orden'}), 400
    
    data = request.get_json() or {}
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    if not _ip_allowed(client_ip):
        return jsonify({'error': 'Operación no permitida desde esta IP'}), 403
    
    changes = {}
    if 'quantity_produced' in data:
        changes['quantity_produced'] = {'old': item.quantity_produced, 'new': data['quantity_produced']}
        item.quantity_produced = float(data['quantity_produced'])
    if 'quantity_shipped' in data:
        changes['quantity_shipped'] = {'old': item.quantity_shipped, 'new': data['quantity_shipped']}
        item.quantity_shipped = float(data['quantity_shipped'])
    if 'status' in data:
        changes['status'] = {'old': item.status, 'new': data['status']}
        item.status = data['status']
    
    db.session.commit()
    
    db.session.add(AuditLog(
        user_id=int(get_jwt_identity()),
        action='update_item',
        entity='item',
        entity_id=str(item.id),
        details=changes
    ))
    db.session.commit()
    
    return jsonify({'message': 'Item actualizado', 'item': {
        'id': item.id,
        'item_code': item.item_code,
        'quantity_ordered': item.quantity_ordered,
        'quantity_produced': item.quantity_produced,
        'quantity_shipped': item.quantity_shipped,
        'status': item.status
    }})


@bp.route('/batch/update-status', methods=['PUT'])
@jwt_required()
def batch_update_status():
    """Actualizar estado a múltiples órdenes"""
    data = request.get_json() or {}
    order_ids = data.get('order_ids', [])
    new_status = data.get('status')
    
    if not order_ids or not new_status:
        return jsonify({'error': 'order_ids y status requeridos'}), 400
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    if not _ip_allowed(client_ip):
        return jsonify({'error': 'Operación no permitida desde esta IP'}), 403
    
    updated = 0
    for oid in order_ids:
        order = Order.query.get(oid)
        if not order:
            continue
        old = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        updated += 1
        
        db.session.add(AuditLog(
            user_id=int(get_jwt_identity()),
            action='batch_update_status',
            entity='order',
            entity_id=str(order.id),
            details={'old': old, 'new': new_status}
        ))
    
    db.session.commit()
    return jsonify({'message': f'{updated} órdenes actualizadas'})


@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_backorder_stats():
    """Obtener estadísticas de backorders"""
    # Total de backorders
    total_backorders = Order.query.filter_by(is_backorder=True).count()
    
    # Por prioridad
    by_priority = {}
    for priority in [1, 2, 3, 4]:
        count = Order.query.filter_by(is_backorder=True, priority=priority).count()
        by_priority[f'priority_{priority}'] = count
    
    # Por estado
    by_status = {}
    for status in ['pending', 'in_production', 'ready', 'shipped']:
        count = Order.query.filter_by(is_backorder=True, status=status).count()
        by_status[status] = count
    
    # Backorders urgentes (prioridad 1 o fecha prometida < 7 días)
    from datetime import timedelta
    urgent_date = datetime.utcnow() + timedelta(days=7)
    urgent_backorders = Order.query.filter(
        Order.is_backorder == True,
        or_(
            Order.priority == 1,
            Order.promised_date <= urgent_date
        )
    ).count()
    
    return jsonify({
        'total_backorders': total_backorders,
        'urgent_backorders': urgent_backorders,
        'by_priority': by_priority,
        'by_status': by_status
    }), 200
