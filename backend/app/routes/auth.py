"""
Rutas de Autenticación
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from datetime import datetime

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['POST'])
def login():
    """Login de usuario"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Usuario inactivo'}), 403
    
    # Crear token JWT
    # JWT v4 requiere que 'sub' sea string
    access_token = create_access_token(identity=str(user.id))
    
    # Actualizar último login
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200


@bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    """Registrar nuevo usuario (solo admin)"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    
    if current_user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not username or not email or not password:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Verificar si usuario existe
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Usuario ya existe'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email ya registrado'}), 400
    
    # Crear usuario
    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'Usuario creado exitosamente',
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'role': new_user.role
        }
    }), 201


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtener información del usuario actual"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }), 200
