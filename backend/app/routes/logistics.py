"""
Rutas de Logística y Entregas
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Order
from sqlalchemy import or_

bp = Blueprint('logistics', __name__)


@bp.route('/pending-shipments', methods=['GET'])
@jwt_required()
def get_pending_shipments():
    """Obtener órdenes pendientes de envío"""
    search = request.args.get('search')
    query = Order.query.filter(
        Order.status.in_(['ready'])
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Order.order_number.ilike(search_term),
            Order.customer_name.ilike(search_term)
        ))

    orders = query.order_by(Order.promised_date.asc()).all()
    
    return jsonify({
        'total': len(orders),
        'shipments': [order.to_dict() for order in orders]
    }), 200


@bp.route('/shipped', methods=['GET'])
@jwt_required()
def get_shipped_orders():
    """Obtener órdenes enviadas"""
    search = request.args.get('search')
    query = Order.query.filter_by(status='shipped')

    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Order.order_number.ilike(search_term),
            Order.customer_name.ilike(search_term)
        ))

    orders = query.order_by(
        Order.updated_at.desc()
    ).limit(50).all()
    
    return jsonify({
        'total': len(orders),
        'shipments': [order.to_dict() for order in orders]
    }), 200


@bp.route('/shipment/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_shipment(order_id):
    """Actualizar información de envío"""
    # data = request.get_json() # Unused for now
    order = Order.query.get_or_404(order_id)
    
    # Update Status
    order.status = 'shipped'
    order.logistics_status = 'shipped'
    
    # TODO: Add tracking_number and carrier to Order model
    # order.tracking_number = data.get('tracking_number')
    # order.carrier = data.get('carrier')

    db.session.commit()
    
    return jsonify({
        'message': 'Orden marcada como enviada',
        'order': order.to_dict()
    }), 200
