"""
Aplicación Backend para Sistema de Backorder PCM
Gestión de backorders para planta de fabricación de etiquetas
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from celery import Celery
import yaml
import os
from datetime import timedelta

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
celery = Celery(__name__)

def load_config():
    """Cargar configuración desde config.yaml"""
    # Buscar primero en /app/config.yaml (montado por Docker)
    config_path = '/app/config.yaml'
    if not os.path.exists(config_path):
        # Fallback a ruta relativa para desarrollo local
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    config = load_config()
    app.config['APP_CONFIG_YAML'] = config
    app.config['OCR_CONFIG'] = config.get('ocr', {}) or {}
    
    # Configuración de Flask
    secret_key = (config.get('server', {}).get('secret_key') or '').strip()
    is_debug = bool(config.get('server', {}).get('debug', False))
    env_name = os.getenv('FLASK_ENV', 'production').lower()
    is_production = env_name == 'production' and not is_debug
    if is_production and (not secret_key or secret_key == 'CHANGE_THIS_IN_PRODUCTION'):
        raise RuntimeError(
            'Configuración insegura: SECRET_KEY inválida. '
            'Configura server.secret_key en config.yaml antes de iniciar en producción.'
        )
    app.config['SECRET_KEY'] = secret_key
    app.config['JWT_SECRET_KEY'] = secret_key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=config['security']['jwt_expiration'])
    
    # Límite de tamaño de archivo (50MB por defecto, configurable)
    max_upload_mb = config.get('upload', {}).get('max_file_size_mb', 50)
    app.config['MAX_CONTENT_LENGTH'] = max_upload_mb * 1024 * 1024  # Convertir MB a bytes
    
    # Configuración de Base de Datos
    db_config = config['database']
    if os.getenv('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"{db_config['type']}://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        )
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración de Celery
    redis_url = os.getenv('REDIS_URL', f"redis://{config['cache']['host']}:{config['cache']['port']}/0")
    app.config['CELERY_BROKER_URL'] = redis_url
    app.config['CELERY_RESULT_BACKEND'] = redis_url
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Bloquear operaciones de admin si debe cambiar contraseña
    @app.before_request
    def enforce_admin_password_change():
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from app.models import User

        # Ignorar solicitudes OPTIONS (preflight CORS)
        if request.method == 'OPTIONS':
            return None

        allowed_paths = {
            '/api/auth/login',
            '/api/auth/change-password',
            '/api/auth/me',
            '/health'
        }
        if request.path in allowed_paths:
            return None

        try:
            verify_jwt_in_request(optional=True)
        except Exception:
            return None

        identity = get_jwt_identity()
        if not identity:
            return None

        user = User.query.get(int(identity))
        if user and user.role == 'admin' and user.must_change_password:
            return jsonify({
                'error': 'Debe cambiar la contraseña antes de continuar',
                'must_change_password': True
            }), 403
    
    # Configurar Celery
    celery.conf.update(app.config)
    
    # Registrar blueprints
    from app.routes import backorder, materials, production, logistics, auth, dashboard, admin, settings, importer
    from app.routes import test_mode

    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(backorder.bp, url_prefix='/api/backorder')
    app.register_blueprint(materials.bp, url_prefix='/api/materials')
    app.register_blueprint(production.bp, url_prefix='/api/production')
    app.register_blueprint(logistics.bp, url_prefix='/api/logistics')
    app.register_blueprint(dashboard.bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    app.register_blueprint(settings.bp, url_prefix='/api/settings')
    app.register_blueprint(importer.bp, url_prefix='/api/import')
    app.register_blueprint(test_mode.bp, url_prefix='/api/test')
    
    # Ruta de salud
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Backorder PCM API Running'}
    
    # Error handler para archivos demasiado grandes
    @app.errorhandler(413)
    def request_entity_too_large(error):
        max_size_mb = app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024) / (1024 * 1024)
        return jsonify({
            'error': f'Archivo demasiado grande. Tamaño máximo permitido: {int(max_size_mb)}MB'
        }), 413
    
    return app

def create_celery_app(app=None):
    """Configurar Celery para tareas asíncronas"""
    app = app or create_app()
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
