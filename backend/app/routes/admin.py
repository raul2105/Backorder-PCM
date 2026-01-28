"""
Rutas de administración (solo para usuarios con rol admin)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, AuditLog

bp = Blueprint('admin', __name__)


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
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
def create_user():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not email or not password:
        return jsonify({'error': 'Datos incompletos'}), 400

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

    db.session.add(AuditLog(user_id=int(get_jwt_identity()), action='create_user', entity='user', entity_id=str(new_user.id), details={'username': username, 'role': role}))
    db.session.commit()

    return jsonify({'message': 'Usuario creado', 'id': new_user.id}), 201


@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    changes = {}

    if 'role' in data:
        changes['role'] = {'old': user.role, 'new': data['role']}
        user.role = data['role']
    if 'is_active' in data:
        changes['is_active'] = {'old': user.is_active, 'new': data['is_active']}
        user.is_active = bool(data['is_active'])
    if 'password' in data and data['password']:
        changes['password'] = 'updated'
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()

    db.session.add(AuditLog(user_id=int(get_jwt_identity()), action='update_user', entity='user', entity_id=str(user.id), details=changes))
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
