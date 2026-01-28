"""
Rutas de Dashboard - Vista general
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models import Order, Material, ProductionLog
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('dashboard', __name__)


@bp.route('/overview', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    """Obtener resumen general del sistema"""
    
    # Backorders totales
    total_backorders = Order.query.filter_by(is_backorder=True).count()
    
    # Backorders urgentes (próximos 7 días)
    urgent_date = datetime.utcnow() + timedelta(days=7)
    urgent_backorders = Order.query.filter(
        Order.is_backorder == True,
        Order.promised_date <= urgent_date
    ).count()
    
    # Órdenes en producción
    in_production = Order.query.filter_by(status='in_production').count()
    
    # Materiales con stock bajo (menos de 100 unidades como ejemplo)
    low_stock_materials = Material.query.filter(
        Material.quantity_available < 100
    ).count()
    
    # Producción de hoy
    today = datetime.utcnow().date()
    today_production = ProductionLog.query.filter(
        func.date(ProductionLog.production_date) == today
    ).count()
    
    # Órdenes completadas esta semana
    week_ago = datetime.utcnow() - timedelta(days=7)
    completed_this_week = Order.query.filter(
        Order.status == 'delivered',
        Order.updated_at >= week_ago
    ).count()
    
    return jsonify({
        'backorders': {
            'total': total_backorders,
            'urgent': urgent_backorders
        },
        'production': {
            'in_progress': in_production,
            'logs_today': today_production
        },
        'inventory': {
            'low_stock_alerts': low_stock_materials
        },
        'completed': {
            'this_week': completed_this_week
        }
    }), 200


@bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Obtener actividad reciente"""
    
    # Últimas órdenes actualizadas
    recent_orders = Order.query.order_by(
        Order.updated_at.desc()
    ).limit(10).all()
    
    # Últimos logs de producción
    recent_production = ProductionLog.query.order_by(
        ProductionLog.production_date.desc()
    ).limit(10).all()
    
    return jsonify({
        'recent_orders': [order.to_dict() for order in recent_orders],
        'recent_production': [{
            'id': log.id,
            'order_id': log.order_id,
            'production_date': log.production_date.isoformat() if log.production_date else None,
            'quantity_produced': log.quantity_produced,
            'status': log.status
        } for log in recent_production]
    }), 200
