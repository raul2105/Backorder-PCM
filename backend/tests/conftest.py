"""
Configuración y fixtures de pytest para los tests
"""

import pytest
import sys
import os
from datetime import datetime

# Agregar el directorio backend al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Order, Customer, AuditLog
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='function')
def app():
    """Crear aplicación Flask para tests"""
    # Crear app con configuración de test
    app = create_app()
    
    # Configurar base de datos en memoria
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Contexto de aplicación
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Cliente de test Flask"""
    return app.test_client()


@pytest.fixture(scope='function')
def test_user(app):
    """Crear usuario de prueba"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpass'),
            role='admin',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture(scope='function')
def test_customer(app):
    """Crear cliente de prueba"""
    with app.app_context():
        customer = Customer(
            customer_code='CUST001',
            name='Test Customer',
            priority_level=2,
            erp_source='manual',
            erp_id='MANUAL-CUST001'
        )
        db.session.add(customer)
        db.session.commit()
        db.session.refresh(customer)
        return customer


@pytest.fixture(scope='function')
def test_order(app, test_customer):
    """Crear orden de prueba"""
    with app.app_context():
        order = Order(
            order_number='BO-2026-001',
            customer_id=test_customer.id,
            customer_name=test_customer.name,
            order_date=datetime.utcnow(),
            promised_date=datetime.utcnow(),
            status='pending',
            priority=2,
            is_backorder=True,
            backorder_reason='Test backorder',
            planning_status='pending',
            warehouse_status='pending',
            purchasing_status='pending',
            production_status='pending',
            logistics_status='pending',
            erp_source='manual'
        )
        db.session.add(order)
        db.session.commit()
        db.session.refresh(order)
        return order


@pytest.fixture(scope='function')
def auth_token(client, test_user):
    """Obtener token JWT de autenticación"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    return data['access_token']


@pytest.fixture(scope='function')
def auth_headers(auth_token):
    """Headers con autenticación JWT"""
    return {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }
