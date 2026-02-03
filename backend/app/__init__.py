"""
Aplicación Backend para Sistema de Backorder PCM
Gestión de backorders para planta de fabricación de etiquetas
"""

from flask import Flask
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
    """
    Cargar configuración desde config.yaml y override con variables de entorno
    Las variables de entorno tienen prioridad sobre config.yaml para secrets
    """
    # Buscar primero en /app/config.yaml (montado por Docker)
    config_path = '/app/config.yaml'
    if not os.path.exists(config_path):
        # Fallback a ruta relativa para desarrollo local
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Override secrets con variables de entorno (más seguro)
    if os.getenv('SECRET_KEY'):
        config['server']['secret_key'] = os.getenv('SECRET_KEY')
    
    if os.getenv('JWT_SECRET_KEY'):
        config['server']['jwt_secret_key'] = os.getenv('JWT_SECRET_KEY')
    
    # Database
    if os.getenv('DB_HOST'):
        config['database']['host'] = os.getenv('DB_HOST')
    if os.getenv('DB_PORT'):
        config['database']['port'] = int(os.getenv('DB_PORT'))
    if os.getenv('DB_NAME'):
        config['database']['name'] = os.getenv('DB_NAME')
    if os.getenv('DB_USER'):
        config['database']['user'] = os.getenv('DB_USER')
    if os.getenv('DB_PASSWORD'):
        config['database']['password'] = os.getenv('DB_PASSWORD')
    
    # ERP Syteline
    if os.getenv('SYTELINE_PASSWORD'):
        config['erp_systems']['syteline']['connection']['password'] = os.getenv('SYTELINE_PASSWORD')
    if os.getenv('SYTELINE_USERNAME'):
        config['erp_systems']['syteline']['connection']['username'] = os.getenv('SYTELINE_USERNAME')
    if os.getenv('SYTELINE_ENABLED'):
        config['erp_systems']['syteline']['enabled'] = os.getenv('SYTELINE_ENABLED').lower() == 'true'
    
    # ERP Mongus
    if os.getenv('MONGUS_API_KEY'):
        config['erp_systems']['mongus']['api_key'] = os.getenv('MONGUS_API_KEY')
    if os.getenv('MONGUS_BASE_URL'):
        config['erp_systems']['mongus']['base_url'] = os.getenv('MONGUS_BASE_URL')
    if os.getenv('MONGUS_ENABLED'):
        config['erp_systems']['mongus']['enabled'] = os.getenv('MONGUS_ENABLED').lower() == 'true'
    
    # ERP Intranet
    if os.getenv('INTRANET_PASSWORD'):
        config['erp_systems']['intranet']['password'] = os.getenv('INTRANET_PASSWORD')
    if os.getenv('INTRANET_USERNAME'):
        config['erp_systems']['intranet']['username'] = os.getenv('INTRANET_USERNAME')
    if os.getenv('INTRANET_ENABLED'):
        config['erp_systems']['intranet']['enabled'] = os.getenv('INTRANET_ENABLED').lower() == 'true'
    
    return config

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Cargar configuración
    config = load_config()
    
    # Configuración de Flask
    app.config['SECRET_KEY'] = config['server']['secret_key']
    # Use separate JWT secret if provided, otherwise use same as SECRET_KEY
    app.config['JWT_SECRET_KEY'] = config['server'].get('jwt_secret_key', config['server']['secret_key'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=config['security']['jwt_expiration'])
    
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
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Backorder PCM API Running'}
    
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
