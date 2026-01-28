"""
Rutas de Materiales - Gestión de inventario
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Material

bp = Blueprint('materials', __name__)


@bp.route('/', methods=['GET'])
@jwt_required()
def get_materials():
    """Obtener lista de materiales"""
    category = request.args.get('category')
    low_stock = request.args.get('low_stock', type=bool)
    
    query = Material.query
    
    if category:
        query = query.filter(Material.category == category)
    
    if low_stock:
        query = query.filter(Material.quantity_available <= Material.minimum_stock)
    
    materials = query.all()
    
    return jsonify({
        'total': len(materials),
        'materials': [{
            'id': m.id,
            'material_code': m.material_code,
            'description': m.description,
            'category': m.category,
            'quantity_available': m.quantity_available,
            'quantity_reserved': m.quantity_reserved,
            'quantity_on_order': m.quantity_on_order,
            'unit': m.unit,
            'minimum_stock': m.minimum_stock,
            'supplier_name': m.supplier_name,
            'lead_time_days': m.lead_time_days
        } for m in materials]
    }), 200


@bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_material_alerts():
    """Obtener alertas de materiales con stock bajo"""
    low_stock_materials = Material.query.filter(
        Material.quantity_available <= Material.minimum_stock
    ).all()
    
    return jsonify({
        'total_alerts': len(low_stock_materials),
        'materials': [{
            'material_code': m.material_code,
            'description': m.description,
            'quantity_available': m.quantity_available,
            'minimum_stock': m.minimum_stock,
            'deficit': m.minimum_stock - m.quantity_available,
            'supplier': m.supplier_name,
            'lead_time_days': m.lead_time_days
        } for m in low_stock_materials]
    }), 200
