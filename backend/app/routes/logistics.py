"""
Rutas de Logística y Entregas
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import Order
from app.middleware import require_allowed_ip, require_roles
from sqlalchemy import or_
from app.services.ocr_service import run_ocr, OCRNotAvailable
from app.services.ocr_matching import token_in_text, OcrValidationResult

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
@require_allowed_ip
@require_roles('logistics')
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


@bp.route('/shipment/<int:order_id>/ocr-validate', methods=['POST'])
@jwt_required()
@require_allowed_ip
@require_roles('logistics')
def ocr_validate_shipment(order_id: int):
    """OCR de etiqueta/packing slip para validar orden/cliente antes de embarcar."""
    order = Order.query.get_or_404(order_id)

    if 'image' not in request.files:
        return jsonify({'error': 'Falta el archivo de imagen (campo: image)'}), 400

    image_file = request.files['image']
    image_bytes = image_file.read() if image_file else b''
    if not image_bytes:
        return jsonify({'error': 'Archivo vacío'}), 400

    try:
        ocr_out = run_ocr(image_bytes)
    except OCRNotAvailable as e:
        return jsonify({'error': str(e)}), 501
    except Exception as e:
        return jsonify({'error': f'Error procesando OCR: {e}'}), 400

    matched_order_number = order.order_number if token_in_text(ocr_out.text, order.order_number) else None
    matched_customer_name = order.customer_name if (order.customer_name and token_in_text(ocr_out.text, order.customer_name)) else None

    result = OcrValidationResult(
        raw_text=ocr_out.text,
        avg_confidence=ocr_out.avg_confidence,
        matched_order_number=matched_order_number,
        matched_customer_name=matched_customer_name,
        matched_item_code=None,
        matched_work_order=None,
    )

    ok = bool(matched_order_number and matched_customer_name)
    return jsonify({
        'order_id': order.id,
        'order_number': order.order_number,
        'avg_confidence': ocr_out.avg_confidence,
        'validation': result.to_dict(),
        'ok': ok
    }), 200
