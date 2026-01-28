# Personalización y Adaptación del Sistema

## Adaptación de Conectores ERP

### INFOR Syteline

El conector en `backend/app/erp_connectors/syteline_connector.py` incluye queries de ejemplo que **deben adaptarse** a tu instalación específica de Syteline.

#### Pasos para Adaptar:

1. **Identificar el esquema de tu base de datos Syteline**

Conecta a tu base de datos Syteline y ejecuta:
```sql
-- Ver tablas disponibles
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- Ver campos de una tabla específica
SELECT COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'co_mst'
ORDER BY ORDINAL_POSITION;
```

2. **Modificar Query de Órdenes**

En `syteline_connector.py`, método `fetch_orders()`, adaptar la query:

```python
# Ejemplo original (líneas 65-83):
query = """
SELECT 
    co.CoNum AS order_number,
    co.CustNum AS customer_id,
    c.Name AS customer_name,
    ...
FROM 
    co_mst co
    INNER JOIN customer_mst c ON co.CustNum = c.CustNum
    ...
"""

# Adaptar según tu esquema:
# - Cambiar nombres de tablas (co_mst, customer_mst, etc.)
# - Cambiar nombres de campos (CoNum, CustNum, etc.)
# - Ajustar JOINs según relaciones en tu BD
```

3. **Modificar Query de Materiales**

En `syteline_connector.py`, método `fetch_materials()`:

```python
# Líneas 98-113
# Adaptar nombres de tablas y campos:
query = """
SELECT 
    i.Item AS material_code,          # Tu campo de código
    i.Description AS description,      # Tu campo de descripción
    ...
FROM 
    item_mst i                         # Tu tabla de items
    LEFT JOIN itemloc_mst il ...       # Tus tablas de inventario
"""
```

4. **Probar las Queries Modificadas**

```powershell
# Probar conexión
docker-compose exec backend python -c "
from app.erp_connectors import ERPConnectorFactory
connector = ERPConnectorFactory.get_connector('syteline')
connector.connect()
print('Conectado correctamente')
connector.disconnect()
"

# Probar obtención de órdenes
docker-compose exec backend python -c "
from app.erp_connectors import ERPConnectorFactory
connector = ERPConnectorFactory.get_connector('syteline')
orders = connector.fetch_orders()
print(f'Obtenidas {len(orders)} órdenes')
if orders:
    print('Ejemplo:', orders[0])
"
```

### MONGUS / Intranet

Para APIs REST, adaptar en los conectores correspondientes:

#### mongus_connector.py:
```python
# Líneas 52-62
def fetch_orders(self, start_date=None, end_date=None):
    # Adaptar endpoint según documentación de tu API
    data = self._make_request('/orders', params=params)
    
    # Adaptar estructura de respuesta:
    if data and 'orders' in data:  # Cambiar según estructura real
        return data['orders']
```

#### intranet_connector.py:
```python
# Similar adaptación según tu API interna
# Verificar:
# - Endpoints correctos
# - Estructura de datos de respuesta
# - Método de autenticación
```

## Personalización de Modelos de Datos

Si necesitas campos adicionales:

### 1. Modificar Modelo

En `backend/app/models/__init__.py`:

```python
class Order(db.Model):
    # ... campos existentes ...
    
    # Agregar campos personalizados:
    custom_field = db.Column(db.String(100))
    notes = db.Column(db.Text)
```

### 2. Crear Migración

```powershell
docker-compose exec backend python -c "
from app import create_app, db
from flask_migrate import init, migrate, upgrade

app = create_app()
with app.app_context():
    # Crear migración
    # migrate()
    
    # O recrear todo (CUIDADO: borra datos)
    db.drop_all()
    db.create_all()
"
```

## Personalización de Reglas de Prioridad

En `backend/app/services/priority_service.py`, método `calculate_priority()`:

```python
def calculate_priority(order):
    score = 0
    
    # Factor 1: Fecha prometida (modificar peso)
    days_until_due = (order.promised_date - datetime.utcnow()).days
    if days_until_due < 0:
        score += 40  # Cambiar estos valores
    elif days_until_due <= 2:
        score += 35  # según tus necesidades
    # ...
    
    # Agregar nuevos factores:
    # Factor 4: Valor de la orden
    if hasattr(order, 'order_value'):
        if order.order_value > 10000:
            score += 15
        elif order.order_value > 5000:
            score += 10
    
    # Ajustar rangos de prioridad:
    if score >= 70:    # Modificar umbrales
        return 1
    elif score >= 50:
        return 2
    elif score >= 30:
        return 3
    else:
        return 4
```

## Personalización de Frontend

### Modificar Colores/Tema

En `frontend/src/App.jsx`:

```javascript
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',  // Color principal (azul)
    },
    secondary: {
      main: '#dc004e',  // Color secundario (rojo)
    },
    // Agregar colores personalizados:
    custom: {
      urgent: '#ff0000',
      warning: '#ff9800',
    }
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',  // Cambiar fuente
  },
});
```

### Agregar Campos a Tablas

En componentes de páginas (ej: `frontend/src/pages/BackorderList.jsx`):

```javascript
<TableHead>
  <TableRow>
    <TableCell>Orden</TableCell>
    <TableCell>Cliente</TableCell>
    {/* Agregar columnas nuevas */}
    <TableCell>Valor</TableCell>
    <TableCell>Notas</TableCell>
    {/* ... */}
  </TableRow>
</TableHead>
```

### Modificar Dashboard

En `frontend/src/pages/Dashboard.jsx`, agregar widgets:

```javascript
const additionalStats = [
  {
    title: 'Mi Métrica',
    value: overview?.custom_metric || 0,
    icon: <CustomIcon />,
    color: '#673ab7',
  }
];
```

## Configuración de Sincronización Automática

### Programar Sincronización con Celery

Crear `backend/app/tasks.py`:

```python
from celery import Celery
from celery.schedules import crontab
from app import create_celery_app
from app.services.sync_service import sync_all_erps

celery = create_celery_app()

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Sincronizar cada 5 minutos
    sender.add_periodic_task(300.0, sync_all_erps.s(), name='sync-erps')
    
    # O usar crontab (cada hora en el minuto 0)
    sender.add_periodic_task(
        crontab(minute=0, hour='*'),
        sync_all_erps.s(),
        name='hourly-sync'
    )
```

## Agregar Nuevos Endpoints API

En `backend/app/routes/`, crear nuevo archivo o agregar a existentes:

```python
# backend/app/routes/custom.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

bp = Blueprint('custom', __name__)

@bp.route('/mi-endpoint', methods=['GET'])
@jwt_required()
def mi_endpoint():
    # Tu lógica aquí
    return jsonify({'mensaje': 'éxito'})
```

Registrar en `backend/app/__init__.py`:

```python
def create_app(config_name='default'):
    # ... código existente ...
    
    from app.routes import custom
    app.register_blueprint(custom.bp, url_prefix='/api/custom')
    
    return app
```

## Cambiar Intervalos de Sincronización

En `config.yaml`:

```yaml
erp_systems:
  syteline:
    sync_interval: 300  # Segundos (300 = 5 minutos)
    # Cambiar según necesidades:
    # 60 = 1 minuto (alta frecuencia, más carga)
    # 600 = 10 minutos
    # 3600 = 1 hora (baja frecuencia)
```

## Backup Automático

Crear script `scripts/backup.ps1`:

```powershell
# Backup diario automático
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "backups/backup_$date.sql"

docker-compose exec -T db pg_dump -U pcm_user backorder_pcm > $backupFile

# Mantener solo últimos 7 días
Get-ChildItem backups/*.sql | 
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | 
    Remove-Item
```

Programar con Tareas Programadas de Windows.

## Testing

Crear tests en `backend/tests/`:

```python
# tests/test_connectors.py
import pytest
from app.erp_connectors import ERPConnectorFactory

def test_syteline_connection():
    connector = ERPConnectorFactory.get_connector('syteline')
    assert connector.test_connection() == True

def test_fetch_orders():
    connector = ERPConnectorFactory.get_connector('syteline')
    orders = connector.fetch_orders()
    assert isinstance(orders, list)
```

Ejecutar:
```powershell
docker-compose exec backend pytest
```

---

Para más información sobre personalización específica, consulta el código fuente con comentarios detallados en cada módulo.
