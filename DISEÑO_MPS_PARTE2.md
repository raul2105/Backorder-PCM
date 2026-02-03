# Diseño MPS - Parte 2: Integración y APIs

## 4. Integración con Sistemas ERP (Syteline/Mongus/Intranet)

### 4.1 Datos a Extraer por Sistema

#### 4.1.1 Syteline (ODBC/SQL Server)

**Demanda (Órdenes):**
```sql
-- Query para órdenes de venta
SELECT 
    co.co_num as order_number,
    co.cust_num as customer_code,
    co.co_ord_date as order_date,
    co.due_date as promised_date,
    co.stat as status,
    co.whse as warehouse,
    coi.item as item_code,
    coi.description as item_description,
    coi.qty_ordered as quantity_ordered,
    coi.qty_shipped as quantity_shipped,
    coi.u_m as unit,
    coi.job as work_order,
    -- Especificaciones custom
    coi.uf_color as color,
    coi.uf_material as material,
    coi.uf_width as width
FROM 
    co_mst co
    INNER JOIN coitem_mst coi ON co.co_num = coi.co_num
WHERE 
    co.stat IN ('O', 'P')  -- Open, Partial
    AND co.type = 'R'  -- Regular orders
    AND coi.qty_ordered > coi.qty_shipped
    AND co.due_date >= @last_sync_date
ORDER BY 
    co.due_date, co.co_num
```

**WIP (Work In Process):**
```sql
-- Query para estado de OT (Jobs)
SELECT
    j.job as work_order,
    j.suffix as suffix,
    j.item as item_code,
    j.stat as status,  -- R=Released, C=Complete
    j.qty_released as quantity_ordered,
    j.qty_complete as quantity_completed,
    jp.oper_num as operation_num,
    jp.wc as work_center,
    jp.setup_hrs_t_lbr as setup_hours,
    jp.run_hrs_t_lbr as run_hours,
    jp.qty_complete as operation_qty_complete,
    jp.stat as operation_status
FROM
    job_mst j
    LEFT JOIN jobroute_mst jp ON j.job = jp.job AND j.suffix = jp.suffix
WHERE
    j.stat IN ('R', 'S')  -- Released, Started
    AND j.type = 'J'  -- Job type
    AND j.LastModifiedDate >= @last_sync_date
ORDER BY
    j.job, jp.oper_num
```

**Inventario de Materiales:**
```sql
-- Query para inventario
SELECT
    i.item as material_code,
    i.description as description,
    i.product_code as category,
    i.u_m as unit,
    il.loc as location,
    il.qty_on_hand as quantity_available,
    il.qty_alloc as quantity_reserved,
    COALESCE(po.qty_ordered, 0) as quantity_on_order,
    i.lead_time as lead_time_days,
    v.name as supplier_name
FROM
    item_mst i
    LEFT JOIN itemloc_mst il ON i.item = il.item
    LEFT JOIN (
        SELECT poi.item, SUM(poi.qty_ordered - poi.qty_received) as qty_ordered
        FROM poitem_mst poi
        INNER JOIN po_mst po ON poi.po_num = po.po_num
        WHERE po.stat = 'O'
        GROUP BY poi.item
    ) po ON i.item = po.item
    LEFT JOIN vendor_mst v ON i.vendor = v.vend_num
WHERE
    il.loc = @primary_warehouse
    AND i.stat = 'A'  -- Active items
ORDER BY
    i.item
```

**BOM y Routings:**
```sql
-- Query para BOM (Bill of Materials)
SELECT
    jb.job as parent_item,
    jb.material as component_item,
    jb.matl_qty_conv as quantity_per,
    jb.u_m as unit,
    i.description as component_description
FROM
    jobbom_mst jb
    INNER JOIN item_mst i ON jb.material = i.item
WHERE
    jb.job IN (SELECT DISTINCT item FROM coitem_mst WHERE stat = 'O')
ORDER BY
    jb.job, jb.oper_num, jb.seq

-- Query para Routings
SELECT
    jr.job as item_code,
    jr.oper_num as operation_seq,
    jr.wc as work_center,
    wc.description as work_center_name,
    jr.setup_rate as setup_time_hours,
    jr.run_rate as run_time_per_unit,
    jr.crew_size as crew_size
FROM
    jobroute_mst jr
    LEFT JOIN wc_mst wc ON jr.wc = wc.wc
WHERE
    jr.job IN (SELECT DISTINCT item FROM coitem_mst WHERE stat = 'O')
ORDER BY
    jr.job, jr.oper_num
```

**Capacidad (Work Centers):**
```sql
-- Query para recursos/work centers
SELECT
    wc.wc as code,
    wc.description as name,
    wc.resource_group as resource_type,
    wc.run_rate_lbr as capacity_per_hour,
    wc.queue_time as queue_time_hours,
    wc.move_time as move_time_hours
FROM
    wc_mst wc
WHERE
    wc.obsolete = 0
ORDER BY
    wc.wc
```

#### 4.1.2 Mongus (API REST)

**Endpoints necesarios:**

```python
# Órdenes
GET /api/v1/orders?status=open&updated_since={timestamp}
Response: {
    "orders": [
        {
            "order_id": "MON-12345",
            "customer_code": "CUST001",
            "order_date": "2024-01-15",
            "due_date": "2024-02-01",
            "items": [
                {
                    "item_code": "ETQ-001",
                    "quantity": 5000,
                    "unit": "metros",
                    "specifications": {
                        "color": "azul",
                        "material": "papel_termico"
                    }
                }
            ]
        }
    ]
}

# WIP
GET /api/v1/production/wip?updated_since={timestamp}
Response: {
    "jobs": [
        {
            "work_order": "WO-2024-001",
            "item_code": "ETQ-001",
            "status": "in_progress",
            "quantity_planned": 5000,
            "quantity_completed": 2500,
            "current_operation": "printing",
            "machine_id": "PRESS-01"
        }
    ]
}

# Inventario
GET /api/v1/inventory?location=main_warehouse
Response: {
    "materials": [
        {
            "material_code": "PAPEL-TERM-80",
            "quantity_available": 15000,
            "unit": "metros",
            "location": "main_warehouse"
        }
    ]
}
```

#### 4.1.3 Intranet (API Custom)

**Endpoints necesarios:**

```python
# Órdenes pendientes
GET /intranet/api/pedidos/pendientes?fecha_desde={date}
Response: {
    "pedidos": [
        {
            "numero_pedido": "PED-2024-100",
            "cliente": "Cliente ABC",
            "fecha_pedido": "2024-01-15",
            "fecha_compromiso": "2024-02-05",
            "items": [...]
        }
    ]
}

# Estado producción
GET /intranet/api/produccion/estado
Response: {
    "ordenes_trabajo": [
        {
            "ot_numero": "OT-2024-050",
            "estado": "en_proceso",
            "maquina": "LINEA-1",
            "operador": "Juan Perez",
            "avance_pct": 65
        }
    ]
}
```

### 4.2 Estrategia de Sincronización

#### 4.2.1 Sync Incremental (Real-time/Frecuente)

**Implementación con cursores:**

```python
# backend/app/services/sync_service.py (extendido)

class ERPSyncService:
    
    def incremental_sync_orders(self, connector, last_sync_cursor):
        """
        Sincronización incremental de órdenes
        """
        # Obtener cursor de última sync
        cursor = SyncCursor.query.filter_by(
            erp_source=connector.name,
            entity_type='orders'
        ).first()
        
        if not cursor:
            # Primera sync - full
            return self.full_sync_orders(connector)
        
        # Sync incremental desde último cursor
        last_sync_time = cursor.last_sync_timestamp
        
        try:
            # Fetch desde ERP
            new_orders = connector.fetch_orders(
                updated_since=last_sync_time
            )
            
            stats = {
                'new': 0,
                'updated': 0,
                'errors': 0
            }
            
            for erp_order in new_orders:
                try:
                    # Buscar orden existente por external_id
                    order = Order.query.filter_by(
                        erp_source=connector.name,
                        erp_id=erp_order['external_id']
                    ).first()
                    
                    if order:
                        # Actualizar existente (upsert)
                        self._update_order_from_erp(order, erp_order)
                        stats['updated'] += 1
                    else:
                        # Crear nueva
                        order = self._create_order_from_erp(erp_order, connector.name)
                        stats['new'] += 1
                    
                    order.last_sync = datetime.utcnow()
                    
                except Exception as e:
                    logger.error(f"Error procesando orden {erp_order.get('order_number')}: {e}")
                    stats['errors'] += 1
            
            # Commit batch
            db.session.commit()
            
            # Actualizar cursor
            cursor.last_sync_timestamp = datetime.utcnow()
            cursor.last_sync_status = 'success'
            cursor.records_processed = stats['new'] + stats['updated']
            db.session.commit()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error en sync incremental: {e}")
            cursor.last_sync_status = 'error'
            cursor.last_error = str(e)
            db.session.commit()
            raise
    
    
    def incremental_sync_wip(self, connector):
        """
        Sincronización de WIP (muy frecuente, crítico para MPS)
        """
        cursor = SyncCursor.query.filter_by(
            erp_source=connector.name,
            entity_type='wip'
        ).first()
        
        last_sync = cursor.last_sync_timestamp if cursor else None
        
        # Obtener WIP del ERP
        wip_data = connector.fetch_wip_state(updated_since=last_sync)
        
        for wip in wip_data:
            # Buscar orden
            order = Order.query.filter_by(
                erp_source=connector.name,
                erp_id=wip['order_external_id']
            ).first()
            
            if not order:
                logger.warning(f"Orden no encontrada para WIP: {wip['work_order']}")
                continue
            
            # Buscar o crear WIP state
            wip_state = WIPState.query.filter_by(
                order_id=order.id,
                order_item_id=wip.get('item_id')
            ).first()
            
            if not wip_state:
                wip_state = WIPState(order_id=order.id)
                db.session.add(wip_state)
            
            # Actualizar estado
            wip_state.status = map_erp_status(wip['status'])
            wip_state.quantity_completed = wip['quantity_completed']
            wip_state.current_operation_seq = wip.get('operation_num')
            wip_state.current_resource_id = self._map_resource(wip.get('work_center'))
            wip_state.last_update_source = connector.name
            wip_state.updated_at = datetime.utcnow()
            
            # Actualizar también order_item
            if wip.get('item_id'):
                order_item = OrderItem.query.get(wip['item_id'])
                if order_item:
                    order_item.quantity_produced = wip['quantity_completed']
        
        db.session.commit()
        
        # Actualizar cursor
        if cursor:
            cursor.last_sync_timestamp = datetime.utcnow()
            cursor.last_sync_status = 'success'
            db.session.commit()
        
        return {'wip_records_updated': len(wip_data)}
```

**Modelo de Cursor:**

```python
# backend/app/models/__init__.py (agregar)

class SyncCursor(db.Model):
    """Cursores para sincronización incremental"""
    __tablename__ = 'sync_cursors'
    
    id = db.Column(db.Integer, primary_key=True)
    erp_source = db.Column(db.String(50), nullable=False)  # syteline, mongus, intranet
    entity_type = db.Column(db.String(50), nullable=False)  # orders, wip, materials, customers
    
    last_sync_timestamp = db.Column(db.DateTime)
    last_sync_status = db.Column(db.String(20))  # success, error, in_progress
    last_error = db.Column(db.Text)
    records_processed = db.Column(db.Integer, default=0)
    
    # Para sync basado en sequence/offset
    last_sequence_number = db.Column(db.BigInteger)
    last_record_id = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('erp_source', 'entity_type', name='uix_erp_entity'),
    )
```

#### 4.2.2 Nightly Reconciliation

**Tarea programada (Celery):**

```python
# backend/app/tasks/reconciliation_tasks.py

from celery import shared_task
from app import db
from app.models import Order, Material, SyncCursor
from app.services.sync_service import ERPSyncService
import logging

logger = logging.getLogger(__name__)


@shared_task
def nightly_full_reconciliation():
    """
    Reconciliación nocturna completa
    Ejecutar a las 2 AM todos los días
    """
    logger.info("Iniciando reconciliación nocturna completa")
    
    sync_service = ERPSyncService()
    report = {
        'start_time': datetime.utcnow(),
        'orders': {},
        'materials': {},
        'wip': {},
        'discrepancies': []
    }
    
    # 1. Full sync de órdenes
    try:
        report['orders'] = sync_service.full_sync_all_orders()
    except Exception as e:
        logger.error(f"Error en sync de órdenes: {e}")
        report['orders']['error'] = str(e)
    
    # 2. Full sync de materiales
    try:
        report['materials'] = sync_service.full_sync_materials()
    except Exception as e:
        logger.error(f"Error en sync de materiales: {e}")
        report['materials']['error'] = str(e)
    
    # 3. Detectar discrepancias
    report['discrepancies'] = detect_discrepancies()
    
    # 4. Cleanup de datos antiguos
    cleanup_old_sync_data(days=90)
    
    # 5. Recalcular prioridades
    from app.services.priority_service import BackorderPriorityService
    BackorderPriorityService.update_all_backorder_priorities()
    
    # 6. Persistir reporte
    report['end_time'] = datetime.utcnow()
    report['duration_seconds'] = (report['end_time'] - report['start_time']).total_seconds()
    
    save_reconciliation_report(report)
    
    logger.info(f"Reconciliación completada en {report['duration_seconds']} segundos")
    
    return report


def detect_discrepancies():
    """
    Detectar discrepancias entre ERP y sistema local
    """
    discrepancies = []
    
    # Ejemplo: órdenes en ERP que no están en local
    # Ejemplo: cantidades que no coinciden
    # Ejemplo: estados inconsistentes
    
    # Query para órdenes con discrepancias
    orders_with_diff = db.session.query(Order).filter(
        Order.last_sync < datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    for order in orders_with_diff:
        discrepancies.append({
            'type': 'stale_order',
            'order_number': order.order_number,
            'last_sync': order.last_sync.isoformat() if order.last_sync else None
        })
    
    return discrepancies
```

### 4.3 Resolución de Conflictos

**Estrategia de resolución:**

```python
class ConflictResolution:
    """
    Resolver conflictos entre datos del ERP y MPS local
    """
    
    @staticmethod
    def resolve_order_conflict(local_order, erp_order):
        """
        Resolver conflicto en datos de orden
        
        Reglas:
        1. Fechas y cantidades: ERP manda (source of truth)
        2. Prioridades y asignaciones MPS: Local manda
        3. WIP/estado producción: ERP manda
        4. Notas y overrides: Local manda
        """
        resolution = {
            'conflicts': [],
            'resolution_applied': []
        }
        
        # Fechas: ERP wins
        if local_order.promised_date != erp_order['promised_date']:
            resolution['conflicts'].append({
                'field': 'promised_date',
                'local_value': local_order.promised_date,
                'erp_value': erp_order['promised_date'],
                'winner': 'erp'
            })
            local_order.promised_date = erp_order['promised_date']
            resolution['resolution_applied'].append('promised_date updated from ERP')
        
        # Cantidades: ERP wins
        if local_order.quantity_ordered != erp_order['quantity']:
            resolution['conflicts'].append({
                'field': 'quantity',
                'local_value': local_order.quantity_ordered,
                'erp_value': erp_order['quantity'],
                'winner': 'erp'
            })
            # Actualizar cantidad pero mantener MPS si no es crítico
            old_qty = local_order.quantity_ordered
            local_order.quantity_ordered = erp_order['quantity']
            
            # Si cambio > 20%, re-planificar
            if abs(erp_order['quantity'] - old_qty) / old_qty > 0.20:
                trigger_replanning(local_order)
                resolution['resolution_applied'].append('replanning_triggered due to quantity change')
        
        # Prioridad: Local wins (calculada por MPS)
        # NO sobrescribir local_order.priority con ERP
        
        # Estado producción: ERP wins
        if local_order.production_status != erp_order['production_status']:
            local_order.production_status = map_erp_production_status(erp_order['production_status'])
            resolution['resolution_applied'].append('production_status updated from ERP')
        
        # MPS plan assignment: Local wins
        # NO sobrescribir current_mps_plan_id
        
        return resolution
    
    
    @staticmethod
    def resolve_wip_conflict(local_wip, erp_wip):
        """
        WIP siempre usa dato del ERP (es tiempo real del piso)
        """
        local_wip.status = erp_wip['status']
        local_wip.quantity_completed = erp_wip['quantity_completed']
        local_wip.current_operation_seq = erp_wip['operation']
        local_wip.actual_start_time = erp_wip.get('start_time')
        local_wip.last_update_source = 'erp_sync'
        
        return {'resolution': 'erp_overwrite', 'reason': 'wip_is_realtime'}
    
    
    @staticmethod
    def resolve_material_conflict(local_material, erp_material):
        """
        Material: ERP manda para available, local manda para allocated
        """
        # Cantidad disponible: ERP
        local_material.quantity_available = erp_material['quantity_on_hand']
        local_material.quantity_on_order = erp_material.get('quantity_on_order', 0)
        
        # Cantidad reservada: mantener local (viene de MPS allocations)
        # NO sobrescribir quantity_reserved ni allocated_quantity
        
        return {'resolution': 'hybrid', 'fields_from_erp': ['quantity_available', 'quantity_on_order']}
```

### 4.4 Resilience Patterns

**Circuit Breaker para ERPs:**

```python
# backend/app/utils/circuit_breaker.py

from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, stop trying
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker para proteger contra ERPs caídos
    """
    
    def __init__(self, name, failure_threshold=5, timeout_seconds=60, half_open_max_calls=3):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
    
    def call(self, func, *args, **kwargs):
        """
        Ejecutar función con circuit breaker
        """
        if self.state == CircuitState.OPEN:
            # Check si ya pasó el timeout
            if datetime.now() - self.last_failure_time > self.timeout:
                logger.info(f"CircuitBreaker {self.name}: Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Resetear contador en éxito"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info(f"CircuitBreaker {self.name}: Recovered, transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Incrementar contador en fallo"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"CircuitBreaker {self.name}: Failed in HALF_OPEN, going back to OPEN")
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.error(f"CircuitBreaker {self.name}: Threshold reached, transitioning to OPEN")
            self.state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    """Excepción cuando circuit breaker está abierto"""
    pass


# Instancias globales por ERP
syteline_breaker = CircuitBreaker('syteline', failure_threshold=5, timeout_seconds=120)
mongus_breaker = CircuitBreaker('mongus', failure_threshold=3, timeout_seconds=60)
intranet_breaker = CircuitBreaker('intranet', failure_threshold=3, timeout_seconds=60)
```

**Uso en conectores:**

```python
# backend/app/erp_connectors/syteline_connector.py (modificar)

from app.utils.circuit_breaker import syteline_breaker, CircuitBreakerOpenError

class SytelineConnector(BaseERPConnector):
    
    def fetch_orders(self, start_date=None, end_date=None):
        """Fetch con circuit breaker y retry"""
        max_retries = 3
        retry_delay = 5  # segundos
        
        for attempt in range(max_retries):
            try:
                # Usar circuit breaker
                return syteline_breaker.call(self._do_fetch_orders, start_date, end_date)
            
            except CircuitBreakerOpenError as e:
                logger.warning(f"Circuit breaker abierto para Syteline: {e}")
                # No reintentar si circuit está abierto
                return []
            
            except Exception as e:
                logger.error(f"Error fetching orders (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
    
    def _do_fetch_orders(self, start_date, end_date):
        """Implementación real del fetch"""
        # Timeout en query
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SET QUERY_TIMEOUT 30")  # 30 segundos
        
        # ... rest of implementation
```

(Continúa en DISEÑO_MPS_PARTE3.md...)
