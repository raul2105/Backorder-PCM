"""
Endpoint para importar CSV diarios de backorders
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import User
from app.services.csv_importer import import_backorders_from_csv, CSVImporterValidator
from app.utils.auth_helpers import get_current_user
from werkzeug.utils import secure_filename
import os
import logging

bp = Blueprint('importer', __name__)
logger = logging.getLogger(__name__)


@bp.route('/csv', methods=['POST'])
@jwt_required()
def upload_csv():
    """
    Importar CSV de backorders con validaciones de seguridad
    """
    user = get_current_user()
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'Archivo no proporcionado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    # Validar archivo antes de guardar
    try:
        CSVImporterValidator.validate_file(file)
    except ValueError as e:
        logger.warning(f"CSV validation failed for user {user.username}: {e}")
        return jsonify({'error': str(e)}), 400

    # Secure filename
    filename = secure_filename(file.filename)
    
    # Guardar en directorio temporal
    upload_dir = '/tmp/backorder_uploads'
    os.makedirs(upload_dir, exist_ok=True)
    
    # Usar nombre único para evitar colisiones
    import uuid
    unique_filename = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(upload_dir, unique_filename)
    
    try:
        file.save(path)
        
        # Validar tamaño después de guardar
        file_size = os.path.getsize(path)
        if file_size > CSVImporterValidator.MAX_FILE_SIZE:
            os.remove(path)
            return jsonify({'error': f'Archivo muy grande (máximo {CSVImporterValidator.MAX_FILE_SIZE} bytes)'}), 400
        
        # Importar con validación
        result = import_backorders_from_csv(path, user_id=user.id)
        
        logger.info(f"CSV import successful by user {user.username}: {result}")
        
        return jsonify({'message': 'Importación completada', **result}), 200
        
    except ValueError as e:
        logger.error(f"CSV import validation error: {e}")
        return jsonify({'error': f'Error de validación: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        return jsonify({'error': 'Error en importación', 'details': str(e)}), 500
    finally:
        # Limpiar archivo temporal
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as e:
            logger.warning(f"Could not delete temp file {path}: {e}")
