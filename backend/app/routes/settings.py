"""
Rutas de configuración del sistema (solo admin)
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, SystemSetting, AuditLog

bp = Blueprint('settings', __name__)


def admin_required():
    user = User.query.get(int(get_jwt_identity()))
    return user and user.role == 'admin'


@bp.route('/network', methods=['GET'])
@jwt_required()
def get_network_settings():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    s = SystemSetting.query.filter_by(key='network.allowed_ips').first()
    return jsonify({'allowed_ips': s.value if s and s.value else []})


@bp.route('/network', methods=['PUT'])
@jwt_required()
def update_network_settings():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.get_json() or {}
    allowed = data.get('allowed_ips', [])
    if not isinstance(allowed, list):
        return jsonify({'error': 'Formato inválido'}), 400

    s = SystemSetting.query.filter_by(key='network.allowed_ips').first()
    if not s:
        s = SystemSetting(key='network.allowed_ips', value=allowed)
        db.session.add(s)
    else:
        s.value = allowed
    db.session.commit()

    db.session.add(AuditLog(user_id=user.id, action='update_setting', entity='setting', entity_id='network.allowed_ips', details={'allowed_ips': allowed}))
    db.session.commit()

    return jsonify({'message': 'Configuración actualizada', 'allowed_ips': allowed})
