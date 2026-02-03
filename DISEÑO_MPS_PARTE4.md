# Diseño MPS - Parte 4: Implementación Incremental y Backlog

## 7. Metodología de Implementación Incremental

### MVP → MPS Completo

La implementación se divide en fases incrementales, cada una con entregables verificables.

---

### FASE 1: MPS Bucket Diario (Capacidad Gruesa)
**Duración estimada:** 2-3 semanas  
**Objetivo:** Planificación básica con asignación día/recurso sin secuenciación fina

#### Entregables:
1. **Modelos de datos básicos:**
   - Tabla `resources` (líneas/máquinas)
   - Tabla `mps_plans` y `mps_plan_items`
   - Tabla `planning_parameters`
   - Migración DB

2. **Algoritmo simplificado:**
   - Priorización multi-criterio (due date + customer + material)
   - Asignación a recurso por disponibilidad (capacidad gruesa por día)
   - NO secuenciación intra-día
   - NO setups

3. **API mínima:**
   - POST `/api/mps/run` (planning simple)
   - GET `/api/mps/plan` (retrieve plan)

4. **UI básica:**
   - Vista de lista de plan items agrupados por recurso/día
   - Filtros básicos

#### Criterios de Aceptación:
- [ ] Se puede ejecutar planning para horizonte de 2 semanas
- [ ] Órdenes se asignan a recursos respetando capacidad diaria básica
- [ ] Plan resultante se persiste en DB
- [ ] API retorna plan con órdenes asignadas
- [ ] UI muestra plan agrupado por recurso/día
- [ ] Priorización funciona (órdenes urgentes primero)

#### Pruebas:
- Crear 50 órdenes de prueba con diferentes due dates
- Ejecutar planning
- Verificar que órdenes urgentes se programan primero
- Verificar que no se excede capacidad diaria básica

---

### FASE 2: Finite Capacity + Secuenciación Simple
**Duración estimada:** 2-3 semanas  
**Objetivo:** Capacidad finita por turno + secuencia básica

#### Entregables:
1. **Modelos extendidos:**
   - Tabla `shift_calendars` (turnos por recurso)
   - Tabla `calendar_exceptions` (holidays, mantenimientos)
   - Campo `sequence_in_shift` en `mps_plan_items`

2. **Algoritmo mejorado:**
   - Capacidad finita a nivel turno (no solo día)
   - Secuenciación simple por prioridad dentro de turno
   - Cálculo básico de start_time/end_time
   - Validación de constraints (tardiness max)

3. **Extensiones API:**
   - GET `/api/mps/plan` con filtro por turno
   - Payload incluye tiempos estimados

4. **UI mejorada:**
   - Vista de plan por turno (tabla)
   - Indicadores de utilización por turno
   - Órdenes en secuencia

#### Criterios de Aceptación:
- [ ] Planning respeta turnos configurados
- [ ] No se excede capacidad por turno
- [ ] Órdenes tienen secuencia asignada dentro de turno
- [ ] Tiempos start/end calculados
- [ ] UI muestra plan por turno con secuencia
- [ ] Se detecta overload por turno

#### Pruebas:
- Configurar 3 turnos/día para 3 recursos
- Crear 100 órdenes
- Ejecutar planning
- Verificar que cada turno tiene órdenes en secuencia
- Verificar que no hay overload

---

### FASE 3: Setups + Tooling + Optimización Multi-Objetivo
**Duración estimada:** 3-4 semanas  
**Objetivo:** Setup-aware scheduling + optimización de secuencia

#### Entregables:
1. **Modelos completos:**
   - Tabla `setup_times` (changeover matrix)
   - Tabla `routings` y `routing_operations`
   - Campo `setup_attributes` en `order_items`
   - Campo `setup_time_minutes` en `mps_plan_items`

2. **Algoritmo completo:**
   - Secuenciación optimizada (minimizar setups)
   - Algoritmo greedy nearest-neighbor para TSP-like
   - Cálculo de setup time por cambio de color/material/tooling
   - Validación de tooling availability
   - Optimización local (swaps)

3. **API completa:**
   - POST `/api/mps/run` con parámetros de optimización
   - GET `/api/mps/kpis` con setup_ratio
   - PUT `/api/mps/override` (lock/move items)

4. **UI avanzada:**
   - Gantt chart básico (timeline view)
   - Visualización de setup times
   - KPI dashboard con setup ratio

#### Criterios de Aceptación:
- [ ] Setup times calculados por cambio de atributos
- [ ] Secuencia minimiza setups dentro de turno
- [ ] Plan incluye setup times explícitos
- [ ] KPIs calculan setup ratio
- [ ] Gantt muestra setup vs run time
- [ ] Override manual funciona (lock/move)

#### Pruebas:
- Configurar setup matrix con tiempos por color/material
- Crear órdenes con diferentes colores (ej. 3 colores: rojo, azul, verde)
- Ejecutar planning
- Verificar que órdenes del mismo color se agrupan
- Verificar que setup ratio es óptimo

---

### FASE 4: WIP Integration + Replanning Incremental
**Duración estimada:** 2-3 semanas  
**Objetivo:** Integración con WIP real + replanning sin recalcular todo

#### Entregables:
1. **Modelos WIP:**
   - Tabla `wip_states`
   - Sync incremental de WIP desde ERP

2. **Replanning incremental:**
   - Algoritmo que respeta órdenes in_progress
   - Replanning solo de lo pendiente
   - Locked items no se replanifican
   - Detección de desvíos (actual vs plan)

3. **API extendida:**
   - GET `/api/wip` (estado real)
   - POST `/api/mps/run` con mode=incremental

4. **UI WIP:**
   - Monitor de WIP real-time
   - Comparación plan vs actual
   - Alertas de desvío

#### Criterios de Aceptación:
- [ ] WIP sync desde ERP funciona
- [ ] Replanning respeta WIP (no replanifica lo que está corriendo)
- [ ] Locked items no se mueven
- [ ] Desvíos detectados y alertados
- [ ] UI muestra plan vs actual

#### Pruebas:
- Crear plan inicial
- Simular WIP (algunas órdenes in_progress)
- Ejecutar replanning incremental
- Verificar que órdenes in_progress no se replanifican
- Agregar nueva orden urgente
- Verificar que replanning inserta la nueva orden sin recalcular todo

---

### FASE 5: Material Allocation + Constraint Validation
**Duración estimada:** 2 semanas  
**Objetivo:** MRP-lite + validación completa de constraints

#### Entregables:
1. **Material MRP:**
   - Tabla `material_allocations`
   - Cálculo de requirements por OT
   - Reservación de materiales en planning
   - Alertas de shortage

2. **Constraints:**
   - Tabla `constraints`
   - Validación de constraints hard/soft
   - Penalty-based soft constraints

3. **API:**
   - GET `/api/mps/exceptions` (shortages, overloads, violations)
   - GET `/api/mps/feasibility` (validate before scheduling)

4. **UI:**
   - Panel de excepciones (shortage, overload, tardiness)
   - Backlog con ready/not-ready indicators

#### Criterios de Aceptación:
- [ ] Materiales se reservan al programar OT
- [ ] Se detecta shortage proyectado
- [ ] Constraints se validan (hard/soft)
- [ ] Excepciones se listan en UI
- [ ] Backlog muestra material ready status

#### Pruebas:
- Crear órdenes con material requirements
- Simular inventory bajo
- Ejecutar planning
- Verificar que órdenes sin material se bloquean
- Verificar que alertas de shortage aparecen

---

### FASE 6: Enhanced Sync + Circuit Breaker
**Duración estimada:** 2 semanas  
**Objetivo:** Integración robusta con ERPs

#### Entregables:
1. **Sync incremental:**
   - Tabla `sync_cursors`
   - Sync incremental de orders/wip/materials
   - Nightly reconciliation

2. **Resilience:**
   - Circuit breaker para cada ERP
   - Retry con backoff exponencial
   - Conflict resolution

3. **Extender conectores ERP:**
   - `fetch_wip_state()`
   - `fetch_bom()`
   - `fetch_routings()`
   - `fetch_capacity()`

#### Criterios de Aceptación:
- [ ] Sync incremental funciona cada 5 minutos
- [ ] Nightly reconciliation detecta discrepancias
- [ ] Circuit breaker protege contra ERP caído
- [ ] Conflictos se resuelven automáticamente
- [ ] Audit log registra todas las syncs

#### Pruebas:
- Simular ERP caído (circuit breaker abre)
- Verificar que sistema sigue operando con datos locales
- Recuperar ERP (circuit breaker cierra)
- Verificar reconciliación nocturna

---

### FASE 7: Advanced UI + Write-back (Opcional)
**Duración estimada:** 3 semanas  
**Objetivo:** UI completo Gantt + publish plan a ERP

#### Entregables:
1. **UI Gantt:**
   - Gantt chart interactivo (drag-and-drop)
   - Zoom/pan
   - Colores por prioridad/estado
   - Tooltips con detalles

2. **Write-back:**
   - Publish plan a ERP (si aplica)
   - Actualizar due dates en ERP
   - Crear WO en ERP desde MPS

#### Criterios de Aceptación:
- [ ] Gantt chart funcional con drag-and-drop
- [ ] Plan se publica a ERP (si aplicable)
- [ ] WOs se crean automáticamente

---

## 8. Backlog Priorizado y Cambios Concretos

### P0 - CRÍTICO (Arreglar de inmediato)

#### P0.1: JWT Identity Bug
**Problema:** `get_jwt_identity()` puede retornar username o user_id inconsistentemente  
**Archivos:**
- `backend/app/routes/backorder.py`
- `backend/app/routes/production.py`
- `backend/app/routes/admin.py`
- Todos los routes que usan `@jwt_required()`

**Solución:**
```python
# Crear helper function en backend/app/utils/auth_helpers.py
def get_current_user_id():
    """Obtener user_id de forma consistente"""
    identity = get_jwt_identity()
    if isinstance(identity, int):
        return identity
    elif isinstance(identity, str):
        # Buscar usuario por username
        user = User.query.filter_by(username=identity).first()
        return user.id if user else None
    return None

def get_current_user():
    """Obtener objeto User completo"""
    user_id = get_current_user_id()
    return User.query.get(user_id) if user_id else None
```

Reemplazar todas las ocurrencias de `get_jwt_identity()` con `get_current_user_id()`.

#### P0.2: Secrets en config.yaml
**Problema:** Passwords y secrets hardcoded en `config.yaml`  
**Archivos:**
- `config.yaml`
- `backend/app/__init__.py`

**Solución:**
```python
# Usar variables de entorno
import os

def load_config():
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Override secrets con env vars
    if os.getenv('SECRET_KEY'):
        config['server']['secret_key'] = os.getenv('SECRET_KEY')
    
    if os.getenv('DB_PASSWORD'):
        config['database']['password'] = os.getenv('DB_PASSWORD')
    
    if os.getenv('SYTELINE_PASSWORD'):
        config['erp_systems']['syteline']['connection']['password'] = os.getenv('SYTELINE_PASSWORD')
    
    # ... etc
    
    return config
```

Crear `.env.example`:
```bash
SECRET_KEY=your_secret_key_here
DB_PASSWORD=your_db_password
SYTELINE_PASSWORD=your_erp_password
JWT_SECRET_KEY=your_jwt_secret
```

#### P0.3: CSV Upload Security
**Problema:** CSV upload sin validación suficiente en `backend/app/services/csv_importer.py`  
**Archivos:**
- `backend/app/services/csv_importer.py`
- `backend/app/routes/importer.py`

**Solución:**
```python
# En csv_importer.py
import csv
import io
from werkzeug.utils import secure_filename

class CSVImporter:
    
    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 10000
    
    @staticmethod
    def validate_file(file):
        """Validar archivo antes de procesar"""
        # Check extension
        filename = secure_filename(file.filename)
        if not filename.endswith('.csv'):
            raise ValueError("Only CSV files allowed")
        
        # Check size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Back to start
        
        if size > CSVImporter.MAX_FILE_SIZE:
            raise ValueError(f"File too large (max {CSVImporter.MAX_FILE_SIZE} bytes)")
        
        return True
    
    @staticmethod
    def sanitize_csv(file_content):
        """Sanitizar contenido CSV"""
        # Detectar encoding
        detected = chardet.detect(file_content)
        encoding = detected['encoding'] or 'utf-8'
        
        # Decodificar
        content = file_content.decode(encoding)
        
        # Remover caracteres peligrosos
        content = content.replace('\x00', '')  # Null bytes
        
        return content
    
    def import_orders(self, file):
        """Import con validación"""
        self.validate_file(file)
        
        content = file.read()
        sanitized = self.sanitize_csv(content)
        
        reader = csv.DictReader(io.StringIO(sanitized))
        
        rows_processed = 0
        for row in reader:
            if rows_processed >= self.MAX_ROWS:
                raise ValueError(f"Too many rows (max {self.MAX_ROWS})")
            
            # Validar cada campo
            self._validate_row(row)
            
            # Process row
            # ...
            
            rows_processed += 1
        
        return rows_processed
    
    def _validate_row(self, row):
        """Validar campos de row"""
        required_fields = ['order_number', 'customer_name', 'due_date']
        
        for field in required_fields:
            if field not in row or not row[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Sanitizar strings
        for key, value in row.items():
            if isinstance(value, str):
                row[key] = value.strip()[:500]  # Max 500 chars
```

#### P0.4: Celery Configuration
**Problema:** Celery mal configurado, puede no estar corriendo correctamente  
**Archivos:**
- `backend/app/__init__.py`
- `backend/celeryworker.py` (crear si no existe)
- `docker-compose.yml`

**Solución:**

Crear `backend/celeryworker.py`:
```python
from app import create_app, create_celery_app

app = create_app()
celery = create_celery_app(app)

if __name__ == '__main__':
    celery.start()
```

Actualizar `docker-compose.yml`:
```yaml
services:
  celery:
    build: ./backend
    command: celery -A celeryworker.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
      - backend
    volumes:
      - ./backend:/app
```

---

### P1 - ALTA PRIORIDAD (Implementar pronto)

#### P1.1: Implementar Modelos MPS Core
**Archivos a crear/modificar:**
- `backend/app/models/__init__.py` - Agregar modelos nuevos:
  - `Resource`
  - `ShiftCalendar`
  - `CalendarException`
  - `MPSPlan`
  - `MPSPlanItem`
  - `PlanningParameter`

**Crear migración:**
```bash
cd backend
flask db migrate -m "Add MPS core models"
flask db upgrade
```

#### P1.2: Implementar MPSService Básico
**Archivo a crear:**
- `backend/app/services/mps_service.py`

**Contenido mínimo (Fase 1):**
```python
class MPSService:
    
    def run_planning(self, horizon_start, horizon_end, parameters, mode='full', filters=None):
        """Run MPS planning"""
        # Implementar según pseudo-código de Fase 1
        pass
    
    def load_demand(self, start_date, end_date):
        """Load orders to schedule"""
        pass
    
    def calculate_priority_scores(self, orders, parameters):
        """Calculate priority scores"""
        pass
    
    def assign_to_resources(self, orders, resources, capacity):
        """Assign orders to resources"""
        pass
```

#### P1.3: API Routes MPS
**Archivo a crear:**
- `backend/app/routes/mps.py`

Implementar endpoints:
- POST `/api/mps/run`
- GET `/api/mps/plan`

Registrar en `backend/app/__init__.py`:
```python
from app.routes import mps
app.register_blueprint(mps.bp, url_prefix='/api/mps')
```

#### P1.4: Frontend MPS Básico
**Archivos a crear:**
- `frontend/src/pages/MPSPlanView.jsx` - Vista básica de lista
- `frontend/src/services/mpsApi.js` - API client

**Agregar ruta en `App.jsx`:**
```jsx
import MPSPlanView from './pages/MPSPlanView';

// En routes
<Route path="/mps/plan" element={<MPSPlanView />} />
```

---

### P2 - MEDIA PRIORIDAD (Después de P0 y P1)

#### P2.1: Implementar WIP Models
- `backend/app/models/__init__.py`: Agregar `WIPState`

#### P2.2: Sync Service Extensions
- Extender `backend/app/services/sync_service.py` con métodos WIP
- Agregar `backend/app/models/__init__.py`: `SyncCursor`

#### P2.3: Setup Times y Routings
- Implementar modelos `SetupTime`, `Routing`, `RoutingOperation`
- Implementar `backend/app/services/mps_sequencing.py`

#### P2.4: Material Allocations
- Implementar modelo `MaterialAllocation`
- Implementar `backend/app/services/mps_material_service.py`

#### P2.5: KPI Calculator
- Implementar `backend/app/services/mps_kpi_calculator.py`
- Endpoint GET `/api/mps/kpis`

#### P2.6: Gantt Chart UI
- Instalar librería: `npm install react-gantt-chart` o similar
- Implementar `frontend/src/pages/MPSGanttView.jsx`

#### P2.7: Exceptions UI
- Implementar `frontend/src/pages/MPSExceptionsView.jsx`
- Endpoint GET `/api/mps/exceptions`

#### P2.8: Circuit Breaker
- Implementar `backend/app/utils/circuit_breaker.py`
- Integrar en todos los ERP connectors

---

## 9. Estructura de Archivos Final

```
Backorder-PCM/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── __init__.py                 # MODIFICAR: Agregar todos los modelos MPS
│   │   ├── services/
│   │   │   ├── mps_service.py              # CREAR: Core MPS service
│   │   │   ├── mps_algorithms.py           # CREAR: Algoritmos de planificación
│   │   │   ├── mps_prioritization.py       # CREAR: Lógica de priorización
│   │   │   ├── mps_sequencing.py           # CREAR: Secuenciación y setups
│   │   │   ├── mps_validation.py           # CREAR: Validaciones y constraints
│   │   │   ├── mps_kpi_calculator.py       # CREAR: Cálculo de KPIs
│   │   │   ├── mps_material_service.py     # CREAR: Material allocations
│   │   │   ├── sync_service.py             # MODIFICAR: Extender con WIP sync
│   │   │   └── priority_service.py         # MODIFICAR: Integrar con MPS
│   │   ├── routes/
│   │   │   ├── mps.py                      # CREAR: Rutas MPS
│   │   │   └── backorder.py                # MODIFICAR: Integrar con MPS
│   │   ├── erp_connectors/
│   │   │   ├── base_connector.py           # MODIFICAR: Agregar métodos MPS
│   │   │   ├── syteline_connector.py       # MODIFICAR: Implementar WIP/BOM/routing
│   │   │   ├── mongus_connector.py         # MODIFICAR: Implementar WIP
│   │   │   └── intranet_connector.py       # MODIFICAR: Implementar WIP
│   │   ├── utils/
│   │   │   ├── auth_helpers.py             # CREAR: Helper para JWT
│   │   │   └── circuit_breaker.py          # CREAR: Circuit breaker
│   │   └── __init__.py                     # MODIFICAR: Registrar blueprint MPS
│   ├── migrations/                          # Generar con flask db migrate
│   ├── celeryworker.py                      # CREAR: Worker Celery
│   └── tasks/
│       └── reconciliation_tasks.py          # CREAR: Tareas de reconciliación
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── MPSGanttView.jsx            # CREAR: Vista Gantt
│   │   │   ├── MPSBacklogView.jsx          # CREAR: Backlog priorizado
│   │   │   ├── MPSExceptionsView.jsx       # CREAR: Excepciones
│   │   │   ├── MPSKPIDashboard.jsx         # CREAR: Dashboard KPIs
│   │   │   ├── MPSPlanningControl.jsx      # CREAR: Control panel
│   │   │   └── MPSWIPMonitor.jsx           # CREAR: Monitor WIP
│   │   ├── components/
│   │   │   └── mps/                        # CREAR: Componentes MPS
│   │   │       ├── GanttChart.jsx
│   │   │       ├── ResourceTimeline.jsx
│   │   │       ├── PriorityBadge.jsx
│   │   │       ├── ReadyStatusIndicator.jsx
│   │   │       ├── ExceptionCard.jsx
│   │   │       ├── KPICard.jsx
│   │   │       └── OverrideDialog.jsx
│   │   ├── services/
│   │   │   └── mpsApi.js                   # CREAR: API client MPS
│   │   └── hooks/
│   │       ├── useMPSPlan.js               # CREAR: Hook para plan
│   │       ├── useMPSKPIs.js               # CREAR: Hook para KPIs
│   │       └── useWIPState.js              # CREAR: Hook para WIP
├── DISEÑO_MPS.md                            # CREADO: Este documento (parte 1)
├── DISEÑO_MPS_PARTE2.md                     # CREADO: Integración y sync
├── DISEÑO_MPS_PARTE3.md                     # CREADO: APIs y UI
├── DISEÑO_MPS_PARTE4.md                     # CREADO: Implementación y backlog
├── .env.example                             # CREAR: Template de secrets
└── config.yaml                              # MODIFICAR: Agregar sección MPS
```

---

## 10. Configuración Sugerida (config.yaml)

Agregar sección MPS:

```yaml
# Configuración MPS (Master Production Schedule)
mps:
  enabled: true
  
  # Horizonte de planificación
  default_horizon_weeks: 8
  bucket_type: shift  # shift, day, week
  
  # Pesos de priorización (suman 1.0)
  priority_weights:
    due_date: 0.40
    customer_priority: 0.25
    material_availability: 0.20
    aging: 0.10
    slack: 0.05
  
  # Reglas de secuenciación
  sequencing:
    minimize_setups: true
    setup_weight: 1.0
    sequence_by_color: true
    sequence_by_material: true
    sequence_by_width: false
  
  # Constraints
  constraints:
    max_wip_per_resource: 5
    min_batch_size_percent: 0.10
    allow_split_orders: true
    max_tardiness_days: 7
    enforce_material_availability: true
  
  # Material planning
  material:
    look_ahead_days: 3
    auto_reserve: true
    critical_items_first: true
  
  # Performance
  performance:
    max_iterations: 1000
    optimization_timeout_seconds: 300
    enable_local_optimization: true
  
  # Sync
  sync:
    wip_sync_interval_seconds: 300  # 5 minutos
    material_sync_interval_seconds: 600  # 10 minutos
    nightly_reconciliation_hour: 2  # 2 AM
```

---

## 11. Pruebas Recomendadas

### Pruebas Unitarias
```python
# tests/test_mps_service.py
def test_priority_calculation():
    # Test que score se calcula correctamente
    pass

def test_capacity_finite_scheduling():
    # Test que no se excede capacidad
    pass

def test_setup_minimization():
    # Test que setups se minimizan
    pass

def test_material_allocation():
    # Test que materiales se reservan
    pass
```

### Pruebas de Integración
```python
# tests/integration/test_mps_full_flow.py
def test_full_planning_flow():
    # Test flujo completo: orders -> planning -> plan persisted
    pass

def test_wip_integration():
    # Test que WIP se respeta en replanning
    pass
```

### Pruebas de Carga
```bash
# tests/load/test_mps_performance.py
# Probar con 1000+ órdenes
# Verificar que planning termina en <5 minutos
```

---

## 12. Documentación de Usuario

Crear guías:
- `docs/MPS_USER_GUIDE.md` - Guía de usuario para planificadores
- `docs/MPS_API_REFERENCE.md` - Referencia completa de APIs
- `docs/MPS_CONFIGURATION.md` - Guía de configuración de parámetros
- `docs/MPS_TROUBLESHOOTING.md` - Solución de problemas comunes

---

## 13. Resumen de Decisiones Clave

### Decisiones Arquitectónicas:
1. **Postgres como operational store** - Todo el MPS lee/escribe a Postgres local, no depende de ERP en tiempo real
2. **Sync incremental con cursores** - Evita full syncs costosos
3. **Circuit breaker para ERPs** - Sistema sigue operando si ERP cae
4. **Conflict resolution automático** - ERP manda en datos transaccionales, MPS manda en planificación
5. **Heurística vs Optimización exacta** - Heurística greedy para velocidad (vs MIP/CP que sería muy lento)
6. **Incremental replanning** - Solo recalcula lo necesario, respeta WIP y locked items
7. **Explainability first** - Cada decisión de planning tiene `planning_notes` explicando por qué
8. **Soft constraints con penalties** - Permite planes "factibles con excepciones"

### Decisiones de Implementación:
1. **Fases incrementales** - MVP primero, features avanzados después
2. **Tests en cada fase** - Criterios de aceptación verificables
3. **API-first** - Backend completo antes de UI avanzado
4. **Security hardening** - Arreglar P0s antes de agregar features

---

## Fin del Diseño

Este diseño proporciona una hoja de ruta completa y detallada para transformar el sistema Backorder-PCM en un MPS real para planta de etiquetas, con:

✅ Definición clara del negocio (horizonte, buckets, KPIs, entidades)  
✅ Modelo de datos completo (15+ tablas nuevas)  
✅ Algoritmo implementable (pseudo-código detallado)  
✅ Integraciones resilientes (sync incremental, circuit breaker, conflict resolution)  
✅ APIs REST completas (7 endpoints con payloads ejemplo)  
✅ UI diseñado (6 pantallas con mockups)  
✅ Plan de implementación (7 fases con criterios de aceptación)  
✅ Backlog priorizado (P0/P1/P2 con archivos específicos)  
✅ Hallazgos P0 identificados (JWT, secrets, CSV security, Celery)  

**¿Listo para comenzar la implementación?**
