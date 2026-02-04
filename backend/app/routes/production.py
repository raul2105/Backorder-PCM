"""
Rutas de Producción
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models import ProductionLog, Order, OrderItem
from app.middleware import require_allowed_ip, require_roles
from datetime import datetime
from app.services.ocr_service import run_ocr, OCRNotAvailable
from app.services.ocr_matching import find_first_token, token_in_text, OcrValidationResult

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


@bp.route('/in-progress-orders', methods=['GET'])
@jwt_required()
def get_in_progress_orders():
    """Obtener órdenes en producción (todas, no solo backorders)."""
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 100, type=int)

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 500:
        page_size = 100

    query = Order.query.filter_by(status='in_production')

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Order.order_number.ilike(search_term)) |
            (Order.customer_name.ilike(search_term))
        )

    total = query.count()
    orders = query.order_by(Order.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'items': [order.to_dict() for order in orders],
        'total': total,
        'page': page,
        'page_size': page_size
    }), 200


@bp.route('/log', methods=['POST'])
@jwt_required()
@require_allowed_ip
@require_roles('production')
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


@bp.route('/order/<int:order_id>/ocr-validate', methods=['POST'])
@jwt_required()
@require_allowed_ip
@require_roles('production')
def ocr_validate_production_order(order_id: int):
    """OCR de etiqueta para validar e identificar producto/OT en producción."""
    order = Order.query.get_or_404(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()

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

    expected_item_codes = [i.item_code for i in items if i.item_code]
    expected_work_orders = [i.work_order for i in items if i.work_order]

    matched_item_code = find_first_token(ocr_out.text, expected_item_codes)
    matched_work_order = find_first_token(ocr_out.text, expected_work_orders)

    matched_order_number = order.order_number if token_in_text(ocr_out.text, order.order_number) else None

    result = OcrValidationResult(
        raw_text=ocr_out.text,
        avg_confidence=ocr_out.avg_confidence,
        matched_order_number=matched_order_number,
        matched_customer_name=order.customer_name if (order.customer_name and token_in_text(ocr_out.text, order.customer_name)) else None,
        matched_item_code=matched_item_code,
        matched_work_order=matched_work_order,
    )

    return jsonify({
        'order_id': order.id,
        'order_number': order.order_number,
        'avg_confidence': ocr_out.avg_confidence,
        'validation': result.to_dict(),
        'ok': bool(matched_order_number or matched_item_code or matched_work_order)
    }), 200
