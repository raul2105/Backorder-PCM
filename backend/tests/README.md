# Tests Backend - Sistema Backorder PCM

## Estructura de Tests

```
backend/tests/
├── __init__.py
├── conftest.py                              # Configuración y fixtures pytest
└── test_backorder_department_status.py      # Tests del endpoint update_department_status
```

## Ejecución de Tests

### Ejecutar todos los tests
```bash
cd backend
pytest
```

### Ejecutar tests específicos
```bash
# Solo tests de department_status
pytest tests/test_backorder_department_status.py

# Un test específico
pytest tests/test_backorder_department_status.py::TestUpdateDepartmentStatus::test_update_department_status_success

# Con verbose
pytest -v

# Con coverage
pytest --cov=app --cov-report=html
```

## Fixtures Disponibles

- `app`: Aplicación Flask configurada para tests (SQLite en memoria)
- `client`: Cliente de test Flask
- `test_user`: Usuario de prueba precreado
- `test_customer`: Cliente de prueba precreado
- `test_order`: Orden de prueba precreada
- `auth_token`: Token JWT válido
- `auth_headers`: Headers con autenticación incluida

## Tests Implementados

### test_backorder_department_status.py

✅ `test_update_department_status_success` - Actualización exitosa de estado departamental
✅ `test_update_department_status_creates_audit_log` - Verificación de creación de audit log
✅ `test_update_department_status_invalid_department` - Validación de departamento inválido
✅ `test_update_department_status_order_not_found` - Manejo de orden inexistente
✅ `test_update_department_status_without_auth` - Rechazo sin autenticación
✅ `test_update_all_valid_departments` - Actualización de todos los departamentos
✅ `test_update_department_status_no_attribute_error` - NO debe haber AttributeError al obtener user_id

## Cobertura de Criterios de Aceptación

✅ PUT /api/backorder/<id>/department-status responde 200 y actualiza department_status
✅ No hay AttributeError por .get() en get_jwt_identity()
✅ Se crea un audit_log asociado al usuario con:
   - action
   - user_id (como integer)
   - entity_id (order_id)
   - details (department, old_status, new_status)
