"""
Tests para el endpoint update_department_status de Backorder
Valida:
- Correcto funcionamiento del endpoint PUT /api/backorder/<id>/department-status
- Obtención correcta del user_id desde JWT (sin AttributeError)
- Creación de audit log asociado al usuario
"""

import pytest
from app.models import Order, AuditLog


class TestUpdateDepartmentStatus:
    """Tests para actualización de estado departamental"""
    
    def test_update_department_status_success(self, client, auth_headers, test_order, test_user, app):
        """Test: Actualizar department_status exitosamente"""
        # Arrange
        order_id = test_order.id
        payload = {
            'department': 'production_status',
            'status': 'in_process'
        }
        
        # Act
        response = client.put(
            f'/api/backorder/{order_id}/department-status',
            json=payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['order']['production_status'] == 'in_process'
        
        # Verificar que la orden se actualizó en BD
        with app.app_context():
            order = Order.query.get(order_id)
            assert order.production_status == 'in_process'
    
    def test_update_department_status_creates_audit_log(self, client, auth_headers, test_order, test_user, app):
        """Test: Se crea audit log correctamente con user_id"""
        # Arrange
        order_id = test_order.id
        payload = {
            'department': 'warehouse_status',
            'status': 'material_available'
        }
        
        # Act
        response = client.put(
            f'/api/backorder/{order_id}/department-status',
            json=payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verificar que se creó el audit log
        with app.app_context():
            audit_log = AuditLog.query.filter_by(
                action='update_dept_status',
                entity='order',
                entity_id=str(order_id)
            ).first()
            
            assert audit_log is not None
            assert audit_log.user_id == test_user.id
            assert audit_log.details['department'] == 'warehouse_status'
            assert audit_log.details['new_status'] == 'material_available'
            assert 'old_status' in audit_log.details
    
    def test_update_department_status_invalid_department(self, client, auth_headers, test_order):
        """Test: Rechazar departamento inválido"""
        # Arrange
        order_id = test_order.id
        payload = {
            'department': 'invalid_department',
            'status': 'some_status'
        }
        
        # Act
        response = client.put(
            f'/api/backorder/{order_id}/department-status',
            json=payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'inválido' in data['error'].lower()
    
    def test_update_department_status_order_not_found(self, client, auth_headers):
        """Test: Error 404 cuando la orden no existe"""
        # Arrange
        order_id = 99999
        payload = {
            'department': 'planning_status',
            'status': 'approved'
        }
        
        # Act
        response = client.put(
            f'/api/backorder/{order_id}/department-status',
            json=payload,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 404
    
    def test_update_department_status_without_auth(self, client, test_order):
        """Test: Rechazar request sin autenticación"""
        # Arrange
        order_id = test_order.id
        payload = {
            'department': 'logistics_status',
            'status': 'ready_to_ship'
        }
        
        # Act
        response = client.put(
            f'/api/backorder/{order_id}/department-status',
            json=payload
        )
        
        # Assert
        assert response.status_code == 401
    
    def test_update_all_valid_departments(self, client, auth_headers, test_order, app):
        """Test: Actualizar todos los departamentos válidos"""
        # Arrange
        order_id = test_order.id
        departments = [
            ('planning_status', 'approved'),
            ('warehouse_status', 'material_available'),
            ('purchasing_status', 'received'),
            ('production_status', 'completed'),
            ('logistics_status', 'shipped')
        ]
        
        # Act & Assert
        for department, status in departments:
            payload = {
                'department': department,
                'status': status
            }
            
            response = client.put(
                f'/api/backorder/{order_id}/department-status',
                json=payload,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['order'][department] == status
        
        # Verificar estado final en BD
        with app.app_context():
            order = Order.query.get(order_id)
            assert order.planning_status == 'approved'
            assert order.warehouse_status == 'material_available'
            assert order.purchasing_status == 'received'
            assert order.production_status == 'completed'
            assert order.logistics_status == 'shipped'
    
    def test_update_department_status_no_attribute_error(self, client, auth_headers, test_order, app):
        """Test: NO debe haber AttributeError al obtener user_id del JWT"""
        # Arrange
        order_id = test_order.id
        payload = {
            'department': 'planning_status',
            'status': 'approved'
        }
        
        # Act
        response = client.put(
            f'/api/backorder/{order_id}/department-status',
            json=payload,
            headers=auth_headers
        )
        
        # Assert
        # Si hubiera AttributeError, la respuesta sería 500 o 401
        assert response.status_code == 200
        
        # Verificar que el audit log tiene user_id como integer
        with app.app_context():
            audit_log = AuditLog.query.filter_by(
                action='update_dept_status',
                entity='order',
                entity_id=str(order_id)
            ).first()
            
            assert audit_log is not None
            assert isinstance(audit_log.user_id, int)
            assert audit_log.user_id > 0
