"""
Endpoint para importar CSV diarios de backorders
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.services.csv_importer import import_backorders_from_csv
import os

bp = Blueprint('importer', __name__)


@bp.route('/csv', methods=['POST'])
@jwt_required()
def upload_csv():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Archivo no proporcionado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    upload_dir = '/tmp'
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, file.filename)
    file.save(path)

    try:
        result = import_backorders_from_csv(path, user_id=user.id)
        return jsonify({'message': 'Importación completada', **result})
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
