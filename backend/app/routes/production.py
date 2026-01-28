"""
Rutas de Producción
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import ProductionLog, Order
from datetime import datetime

bp = Blueprint('production', __name__)


@bp.route('/logs', methods=['GET'])
@jwt_required()
def get_production_logs():
    """Obtener logs de producción"""
    order_id = request.args.get('order_id', type=int)
    date_from = request.args.get('date_from')
    
    query = ProductionLog.query
    
    if order_id:
        query = query.filter(ProductionLog.order_id == order_id)
    
    if date_from:
        query = query.filter(ProductionLog.production_date >= datetime.fromisoformat(date_from))
    
    logs = query.order_by(ProductionLog.production_date.desc()).all()
    
    return jsonify({
        'total': len(logs),
        'logs': [{
            'id': log.id,
            'order_id': log.order_id,
            'production_date': log.production_date.isoformat() if log.production_date else None,
            'machine_id': log.machine_id,
            'operator': log.operator,
            'quantity_produced': log.quantity_produced,
            'quantity_rejected': log.quantity_rejected,
            'status': log.status,
            'notes': log.notes
        } for log in logs]
    }), 200


@bp.route('/log', methods=['POST'])
@jwt_required()
def create_production_log():
    """Crear log de producción"""
    data = request.get_json()
    
    new_log = ProductionLog(
        order_id=data.get('order_id'),
        machine_id=data.get('machine_id'),
        operator=data.get('operator'),
        quantity_produced=data.get('quantity_produced', 0),
        quantity_rejected=data.get('quantity_rejected', 0),
        status=data.get('status', 'in_progress'),
        notes=data.get('notes')
    )
    
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({
        'message': 'Log de producción creado',
        'log_id': new_log.id
    }), 201
