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
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.models import User
from app.services.csv_importer import import_backorders_from_csv
from app.middleware import require_allowed_ip
import os
import tempfile

bp = Blueprint('importer', __name__)
logger = logging.getLogger(__name__)

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'csv'}
ALLOWED_MIME_TYPES = {'text/csv', 'application/csv', 'text/plain'}


def allowed_file(filename):
    """Validar que el archivo tenga extensión CSV"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/csv', methods=['POST'])
@jwt_required()
@require_allowed_ip
def upload_csv():
    """
    Importar CSV de backorders con validaciones de seguridad
    """
    user = get_current_user()
    Endpoint seguro para importar CSV de backorders.
    
    Validaciones de seguridad:
    - Solo usuarios admin
    - Solo archivos .csv
    - Validación de MIME type
    - Límite de tamaño (configurado en MAX_CONTENT_LENGTH)
    - Nombre de archivo sanitizado (secure_filename)
    - Archivo temporal seguro (tempfile)
    - Limpieza garantizada del archivo temporal
    """
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != 'admin':
        return jsonify({'error': 'No autorizado'}), 403

    # Validar que se envió un archivo
    if 'file' not in request.files:
        return jsonify({'error': 'Archivo no proporcionado'}), 400

    file = request.files['file']
    
    # Validar que el nombre no esté vacío
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
    # Validar extensión del archivo
    if not allowed_file(file.filename):
        return jsonify({
            'error': 'Extensión de archivo no permitida. Solo se permiten archivos .csv'
        }), 400

    # Validar MIME type si está disponible
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        return jsonify({
            'error': f'Tipo de contenido no permitido: {file.content_type}. Se esperaba text/csv'
        }), 400

    # Sanitizar el nombre del archivo para evitar path traversal
    original_filename = file.filename
    safe_filename = secure_filename(original_filename)
    
    if not safe_filename:
        return jsonify({'error': 'Nombre de archivo inválido'}), 400

    # Crear archivo temporal seguro
    # delete=False porque lo eliminaremos manualmente en el finally
    temp_file = None
    temp_path = None
    
    try:
        # Crear archivo temporal con sufijo .csv
        temp_file = tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.csv',
            prefix='backorder_import_',
            delete=False
        )
        temp_path = temp_file.name
        
        # Guardar el contenido del archivo subido en el archivo temporal
        file.save(temp_path)
        temp_file.close()
        
        # Procesar el archivo CSV
        result = import_backorders_from_csv(temp_path, user_id=user.id)
        
        return jsonify({
            'message': 'Importación completada',
            'filename': safe_filename,
            **result
        }), 200
        
    except Exception as e:
        # Log del error (en producción usar logger)
        return jsonify({
            'error': f'Error al procesar el archivo: {str(e)}'
        }), 500
        
    finally:
        # Garantizar que el archivo temporal se elimine SIEMPRE
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError as e:
                # Log del error pero no fallar
                pass
