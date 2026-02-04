"""
Tests de seguridad para IP Allowlist
Valida que los endpoints de escritura bloqueen IPs no permitidas
"""

import pytest
from app import create_app, db
from app.models import User, SystemSetting
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Crear aplicación de prueba"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        
        # Crear usuario admin de prueba
        admin = User(
            username='admin_test',
            email='admin@test.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de prueba"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Obtener headers de autenticación"""
    response = client.post('/api/auth/login', json={
        'username': 'admin_test',
        'password': 'admin123'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}


class TestIPAllowlist:
    """Tests de allowlist de IPs"""
    
    def test_write_endpoint_without_allowlist_allows_all(self, client, auth_headers, app):
        """Sin configuración de allowlist, todos los accesos están permitidos"""
        with app.app_context():
            # Sin configuración de allowlist
            response = client.post(
                '/api/backorder',
                headers=auth_headers,
                json={
                    'order_number': 'TEST-001',
                    'customer_code': 'CUST-001',
                    'promised_date': '2026-02-01T00:00:00',
                    'items': []
                }
            )
            # No debe bloquear (por defecto permite si no hay config)
            assert response.status_code in [201, 400, 500]  # No debe ser 403
    
    def test_write_endpoint_with_empty_allowlist_allows_all(self, client, auth_headers, app):
        """Con allowlist vacía, todos los accesos están permitidos"""
        with app.app_context():
            # Configurar allowlist vacía
            setting = SystemSetting(key='network.allowed_ips', value=[])
            db.session.add(setting)
            db.session.commit()
            
            response = client.post(
                '/api/backorder',
                headers=auth_headers,
                json={
                    'order_number': 'TEST-002',
                    'customer_code': 'CUST-002',
                    'promised_date': '2026-02-01T00:00:00',
                    'items': []
                }
            )
            # No debe bloquear
            assert response.status_code != 403
    
    def test_write_endpoint_blocks_non_allowed_ip(self, client, auth_headers, app):
        """Endpoint de escritura bloquea IP no permitida"""
        with app.app_context():
            # Configurar allowlist que NO incluye 127.0.0.1
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.1.100'])
            db.session.add(setting)
            db.session.commit()
            
            response = client.post(
                '/api/backorder',
                headers=auth_headers,
                json={
                    'order_number': 'TEST-003',
                    'customer_code': 'CUST-003',
                    'promised_date': '2026-02-01T00:00:00',
                    'items': []
                }
            )
            # Debe bloquear con 403
            assert response.status_code == 403
            assert 'no permitida' in response.json['error'].lower()
    
    def test_write_endpoint_allows_exact_ip_match(self, client, auth_headers, app):
        """Endpoint permite IP que coincide exactamente con la allowlist"""
        with app.app_context():
            # Configurar allowlist que incluye 127.0.0.1 (IP del test client)
            setting = SystemSetting(key='network.allowed_ips', value=['127.0.0.1'])
            db.session.add(setting)
            db.session.commit()
            
            response = client.post(
                '/api/backorder',
                headers=auth_headers,
                json={
                    'order_number': 'TEST-004',
                    'customer_code': 'CUST-004',
                    'promised_date': '2026-02-01T00:00:00',
                    'items': []
                }
            )
            # No debe bloquear
            assert response.status_code != 403
    
    def test_write_endpoint_allows_cidr_range(self, client, auth_headers, app):
        """Endpoint permite IP dentro de rango CIDR"""
        with app.app_context():
            # Configurar allowlist con rango CIDR que incluye 127.0.0.1
            setting = SystemSetting(key='network.allowed_ips', value=['127.0.0.0/8'])
            db.session.add(setting)
            db.session.commit()
            
            response = client.post(
                '/api/backorder',
                headers=auth_headers,
                json={
                    'order_number': 'TEST-005',
                    'customer_code': 'CUST-005',
                    'promised_date': '2026-02-01T00:00:00',
                    'items': []
                }
            )
            # No debe bloquear
            assert response.status_code != 403
    
    def test_read_endpoint_not_affected_by_allowlist(self, client, auth_headers, app):
        """Endpoints de lectura NO están afectados por allowlist"""
        with app.app_context():
            # Configurar allowlist restrictiva
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.1.100'])
            db.session.add(setting)
            db.session.commit()
            
            # GET backorders debe funcionar sin importar la IP
            response = client.get(
                '/api/backorder',
                headers=auth_headers
            )
            # No debe bloquear (lectura está permitida)
            assert response.status_code == 200
    
    def test_login_not_affected_by_allowlist(self, client, app):
        """Login NO está afectado por allowlist"""
        with app.app_context():
            # Configurar allowlist restrictiva
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.1.100'])
            db.session.add(setting)
            db.session.commit()
            
            # Login debe funcionar sin importar la IP
            response = client.post('/api/auth/login', json={
                'username': 'admin_test',
                'password': 'admin123'
            })
            # No debe bloquear
            assert response.status_code == 200
            assert 'access_token' in response.json
    
    def test_multiple_write_endpoints_protected(self, client, auth_headers, app):
        """Múltiples endpoints de escritura están protegidos"""
        with app.app_context():
            # Configurar allowlist restrictiva
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.1.100'])
            db.session.add(setting)
            db.session.commit()
            
            # POST backorder
            response = client.post('/api/backorder', headers=auth_headers, json={
                'order_number': 'T', 'customer_code': 'C', 'items': []
            })
            assert response.status_code == 403
            
            # POST register
            response = client.post('/api/auth/register', headers=auth_headers, json={
                'username': 'test', 'email': 'test@test.com', 'password': 'pass'
            })
            assert response.status_code == 403
            
            # PUT network settings
            response = client.put('/api/settings/network', headers=auth_headers, json={
                'allowed_ips': []
            })
            assert response.status_code == 403
    
    def test_x_forwarded_for_when_trust_proxy_disabled(self, client, auth_headers, app):
        """X-Forwarded-For es ignorado cuando trust_proxy está deshabilitado"""
        with app.app_context():
            # Configurar allowlist que incluye la IP del proxy pero no 127.0.0.1
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.1.50'])
            db.session.add(setting)
            db.session.commit()
            
            # Intentar con X-Forwarded-For (debe usar remote_addr en su lugar)
            headers = {**auth_headers, 'X-Forwarded-For': '192.168.1.50'}
            response = client.post(
                '/api/backorder',
                headers=headers,
                json={
                    'order_number': 'TEST-XFF',
                    'customer_code': 'CUST-XFF',
                    'items': []
                }
            )
            # Como trust_proxy=False por defecto, usa remote_addr (127.0.0.1)
            # que NO está en la allowlist [192.168.1.50]
            assert response.status_code == 403
    
    def test_invalid_cidr_notation_handled(self, client, auth_headers, app):
        """Notación CIDR inválida no causa error"""
        with app.app_context():
            # Configurar allowlist con CIDR inválido
            setting = SystemSetting(key='network.allowed_ips', value=[
                'invalid-cidr/99',
                '127.0.0.1'  # Pero incluir la IP válida
            ])
            db.session.add(setting)
            db.session.commit()
            
            response = client.post(
                '/api/backorder',
                headers=auth_headers,
                json={
                    'order_number': 'TEST-CIDR',
                    'customer_code': 'CUST-CIDR',
                    'items': []
                }
            )
            # No debe causar error, debe permitir por la regla válida
            assert response.status_code != 403


class TestAllWriteEndpointsProtected:
    """Validar que TODOS los endpoints de escritura están protegidos"""
    
    def test_all_post_endpoints_protected(self, client, auth_headers, app):
        """Todos los endpoints POST están protegidos (excepto login)"""
        with app.app_context():
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.99.99'])
            db.session.add(setting)
            db.session.commit()
            
            endpoints = [
                '/api/backorder',
                '/api/auth/register',
                '/api/admin/users',
                '/api/import/csv',
                '/api/production/log',
                '/api/admin/tasks/sync-erps'
            ]
            
            for endpoint in endpoints:
                response = client.post(endpoint, headers=auth_headers, json={})
                assert response.status_code == 403, f"Endpoint {endpoint} no está protegido"
    
    def test_all_put_endpoints_protected(self, client, auth_headers, app):
        """Todos los endpoints PUT están protegidos"""
        with app.app_context():
            setting = SystemSetting(key='network.allowed_ips', value=['192.168.99.99'])
            db.session.add(setting)
            db.session.commit()
            
            endpoints = [
                '/api/backorder/1/department-status',
                '/api/backorder/1/priority',
                '/api/backorder/1/status',
                '/api/backorder/1/items/1',
                '/api/backorder/batch/update-status',
                '/api/admin/users/1',
                '/api/settings/network',
                '/api/logistics/shipment/1'
            ]
            
            for endpoint in endpoints:
                response = client.put(endpoint, headers=auth_headers, json={})
                assert response.status_code == 403, f"Endpoint {endpoint} no está protegido"
