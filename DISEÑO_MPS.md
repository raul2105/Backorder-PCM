# Diseño de Master Production Schedule (MPS) para Planta de Etiquetas

## 1. Definición del MPS para Planta de Etiquetas

### 1.1 Horizonte y Bucketing

**Horizonte de Planificación:**
- **Corto Plazo:** 2 semanas (planificación detallada, día/turno)
- **Mediano Plazo:** 4-8 semanas (planificación por día)
- **Largo Plazo:** 8-12 semanas (planificación semanal, capacidad agregada)

**Bucket (Unidad de Tiempo):**
- **Bucket Primario:** Turno (3 turnos/día típicamente: 6am-2pm, 2pm-10pm, 10pm-6am)
- **Bucket Secundario:** Día (para horizonte medio)
- **Bucket Terciario:** Semana (para horizonte largo)

**Unidades de Medida:**
- **Órdenes de Trabajo (OT):** Unidad principal de programación
- **Pedidos/Líneas:** Items individuales de cliente
- **Metros Lineales:** Medida de producción para etiquetas en rollo
- **Rollos/Unidades:** Producto terminado empacado
- **Setups:** Número de cambios de formato/material/color

### 1.2 KPIs del MPS

**KPIs de Cumplimiento:**
- **OTIF (On Time In Full):** % de órdenes entregadas a tiempo y completas (Target: >95%)
- **Tardiness Total:** Suma de días de retraso ponderado por prioridad (Target: <50 días-orden/semana)
- **Fill Rate:** % de demanda cumplida vs solicitada (Target: >98%)

**KPIs de Eficiencia:**
- **Throughput:** Metros lineales producidos / turno (Target: según capacidad nominal)
- **Utilización de Capacidad:** % tiempo productivo vs disponible (Target: 80-90%)
- **Setup Time Ratio:** % tiempo setup vs tiempo total (Target: <15%)
- **WIP (Work In Process):** Órdenes en proceso (Target: <20 OT simultáneas)

**KPIs de Materiales:**
- **Material Availability:** % de OT con materiales completos (Target: >90%)
- **Shortage Impact:** OT bloqueadas por falta material (Target: <5%)
- **Inventory Turns:** Rotación de inventario (Target: >8x/año)

**KPIs de Planificación:**
- **Plan Stability:** % del plan que no cambia semana a semana (Target: >70%)
- **Schedule Attainment:** % del plan ejecutado vs planificado (Target: >85%)
- **Feasibility Score:** % de plan factible (sin violaciones) (Target: 100%)

### 1.3 Entidades del Negocio

**Demanda:**
- Órdenes de venta (backorders actuales + nuevas órdenes)
- Forecast/pronóstico (si aplica)
- Órdenes urgentes/especiales
- Reprocesos/rechazos

**MPS Plan:**
- Plan maestro con OT asignadas a recursos, fechas y turnos
- Secuencia óptima dentro de cada turno
- Tiempos estimados (setup + run)
- Estado: draft, approved, active, archived

**MRP-lite (Material Requirements):**
- Consumo de materiales por OT (BOM)
- Reservaciones/allocations por OT programada
- Alertas de shortage proyectado
- Sugerencias de compra

**Capacidad:**
- Recursos (líneas/máquinas/work centers)
- Calendarios (turnos, días laborables, holidays)
- Disponibilidad efectiva (mantenimientos, downtime histórico)
- Tooling/herramental disponible

**WIP Feedback:**
- Estado real de OT en piso (not started, in progress, completed, on hold)
- Cantidad producida vs planeada
- Operación actual y siguiente
- Problemas/excepciones reportadas
- Tiempos reales (inicio, fin, setup, run)

## 2. Modelo de Datos Propuesto (PostgreSQL + SQLAlchemy)

### 2.1 Tablas Nuevas - Recursos y Capacidad

```sql
-- Recursos/Máquinas/Work Centers
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    resource_type VARCHAR(50) NOT NULL, -- line, machine, work_center, tooling
    status VARCHAR(50) DEFAULT 'active', -- active, maintenance, disabled
    capacity_per_hour FLOAT, -- capacidad nominal (metros/hora, unidades/hora)
    capacity_unit VARCHAR(20), -- metros, unidades, rollos
    setup_capability JSON, -- capacidades de setup: {colors: [...], materials: [...]}
    cost_per_hour FLOAT DEFAULT 0,
    utilization_target FLOAT DEFAULT 0.85, -- target de utilización
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_resources_code ON resources(code);
CREATE INDEX idx_resources_type_status ON resources(resource_type, status);

-- Calendarios y Turnos
CREATE TABLE shift_calendars (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    shift_name VARCHAR(50) NOT NULL, -- Turno 1, Turno 2, Turno 3
    day_of_week INTEGER NOT NULL, -- 0=Lunes, 6=Domingo
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    capacity_percentage FLOAT DEFAULT 1.0, -- ajuste de capacidad (ej. 0.8 = 80% eficiencia)
    notes TEXT
);

CREATE INDEX idx_shift_calendars_resource ON shift_calendars(resource_id, is_active);

-- Excepciones de Calendario (holidays, mantenimientos)
CREATE TABLE calendar_exceptions (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    exception_date DATE NOT NULL,
    exception_type VARCHAR(50) NOT NULL, -- holiday, maintenance, downtime
    start_time TIME,
    end_time TIME,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_calendar_exceptions_resource_date ON calendar_exceptions(resource_id, exception_date);
```

### 2.2 Tablas Nuevas - Routings y Operaciones

```sql
-- Routings (Rutas de Producción)
CREATE TABLE routings (
    id SERIAL PRIMARY KEY,
    item_code VARCHAR(100) NOT NULL,
    routing_name VARCHAR(200),
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_routings_item_active ON routings(item_code, is_active);

-- Operaciones en Routing
CREATE TABLE routing_operations (
    id SERIAL PRIMARY KEY,
    routing_id INTEGER REFERENCES routings(id) ON DELETE CASCADE,
    operation_seq INTEGER NOT NULL, -- secuencia: 10, 20, 30...
    operation_name VARCHAR(200) NOT NULL,
    resource_type VARCHAR(50), -- tipo de recurso requerido
    setup_time_minutes FLOAT DEFAULT 0, -- tiempo de setup base
    run_time_per_unit FLOAT NOT NULL, -- tiempo por unidad (minutos/metro, minutos/rollo)
    run_time_unit VARCHAR(20), -- metro, rollo, unidad
    crew_size INTEGER DEFAULT 1, -- operadores requeridos
    is_outsourced BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE INDEX idx_routing_operations_routing ON routing_operations(routing_id, operation_seq);

-- Tiempos de Setup (Changeover Matrix)
CREATE TABLE setup_times (
    id SERIAL PRIMARY KEY,
    resource_id INTEGER REFERENCES resources(id) ON DELETE CASCADE,
    from_attribute_type VARCHAR(50) NOT NULL, -- color, material, width, tooling
    from_attribute_value VARCHAR(100) NOT NULL,
    to_attribute_type VARCHAR(50) NOT NULL,
    to_attribute_value VARCHAR(100) NOT NULL,
    setup_time_minutes FLOAT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_setup_times_resource ON setup_times(resource_id, from_attribute_type, to_attribute_type);
```

### 2.3 Tablas Nuevas - MPS Plan

```sql
-- Plan Maestro de Producción
CREATE TABLE mps_plans (
    id SERIAL PRIMARY KEY,
    plan_name VARCHAR(200) NOT NULL,
    plan_version INTEGER DEFAULT 1,
    plan_status VARCHAR(50) DEFAULT 'draft', -- draft, approved, active, archived
    horizon_start_date DATE NOT NULL,
    horizon_end_date DATE NOT NULL,
    bucket_type VARCHAR(20) DEFAULT 'shift', -- shift, day, week
    planning_parameters JSON, -- parámetros usados: weights, rules, constraints
    objective_value FLOAT, -- valor de función objetivo (si se optimiza)
    feasibility_score FLOAT, -- % de plan factible
    kpis JSON, -- KPIs calculados del plan
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mps_plans_status_dates ON mps_plans(plan_status, horizon_start_date, horizon_end_date);

-- Items del Plan (OT asignadas)
CREATE TABLE mps_plan_items (
    id SERIAL PRIMARY KEY,
    mps_plan_id INTEGER REFERENCES mps_plans(id) ON DELETE CASCADE,
    order_item_id INTEGER REFERENCES order_items(id),
    order_id INTEGER REFERENCES orders(id),
    
    -- Asignación
    resource_id INTEGER REFERENCES resources(id),
    scheduled_date DATE NOT NULL,
    scheduled_shift VARCHAR(50), -- Turno 1, Turno 2, Turno 3
    sequence_in_shift INTEGER, -- secuencia dentro del turno
    
    -- Tiempos
    setup_time_minutes FLOAT DEFAULT 0,
    run_time_minutes FLOAT NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    
    -- Cantidades
    planned_quantity FLOAT NOT NULL,
    planned_unit VARCHAR(20),
    
    -- Estado y Control
    status VARCHAR(50) DEFAULT 'planned', -- planned, locked, in_progress, completed, cancelled
    is_locked BOOLEAN DEFAULT FALSE, -- bloqueo manual
    priority_override INTEGER, -- override de prioridad
    
    -- Material
    material_allocated BOOLEAN DEFAULT FALSE,
    material_allocation_id INTEGER,
    
    -- Metadata
    planning_notes TEXT, -- explicación de decisión
    constraint_violations JSON, -- violaciones detectadas
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mps_plan_items_plan ON mps_plan_items(mps_plan_id, scheduled_date, resource_id);
CREATE INDEX idx_mps_plan_items_order ON mps_plan_items(order_id, order_item_id);
CREATE INDEX idx_mps_plan_items_resource_date ON mps_plan_items(resource_id, scheduled_date, sequence_in_shift);
```

### 2.4 Tablas Nuevas - WIP y Ejecución

```sql
-- Estado WIP (Work In Process)
CREATE TABLE wip_states (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    order_item_id INTEGER REFERENCES order_items(id),
    mps_plan_item_id INTEGER REFERENCES mps_plan_items(id),
    
    -- Estado Actual
    current_operation_seq INTEGER,
    current_resource_id INTEGER REFERENCES resources(id),
    status VARCHAR(50) NOT NULL, -- not_started, in_progress, on_hold, completed, cancelled
    
    -- Progreso
    quantity_completed FLOAT DEFAULT 0,
    quantity_unit VARCHAR(20),
    completion_percentage FLOAT DEFAULT 0,
    
    -- Tiempos Reales
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    actual_setup_time_minutes FLOAT,
    actual_run_time_minutes FLOAT,
    
    -- Excepciones
    has_exception BOOLEAN DEFAULT FALSE,
    exception_type VARCHAR(100), -- material_shortage, machine_breakdown, quality_issue
    exception_details TEXT,
    
    -- Tracking
    operator VARCHAR(100),
    last_update_source VARCHAR(50), -- erp_sync, manual, sensor
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wip_states_order ON wip_states(order_id, order_item_id);
CREATE INDEX idx_wip_states_resource_status ON wip_states(current_resource_id, status);
CREATE INDEX idx_wip_states_status ON wip_states(status, has_exception);

-- Reservaciones de Material
CREATE TABLE material_allocations (
    id SERIAL PRIMARY KEY,
    material_id INTEGER REFERENCES materials(id),
    mps_plan_item_id INTEGER REFERENCES mps_plan_items(id),
    order_item_id INTEGER REFERENCES order_items(id),
    
    quantity_allocated FLOAT NOT NULL,
    quantity_unit VARCHAR(20),
    allocation_date DATE NOT NULL,
    
    status VARCHAR(50) DEFAULT 'reserved', -- reserved, consumed, released
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_material_allocations_material ON material_allocations(material_id, status);
CREATE INDEX idx_material_allocations_plan_item ON material_allocations(mps_plan_item_id);
```

### 2.5 Tablas Nuevas - Parámetros y Constraints

```sql
-- Parámetros de Planificación
CREATE TABLE planning_parameters (
    id SERIAL PRIMARY KEY,
    parameter_set_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Horizonte
    horizon_weeks INTEGER DEFAULT 8,
    bucket_type VARCHAR(20) DEFAULT 'shift',
    
    -- Pesos de Priorización
    weight_due_date FLOAT DEFAULT 0.4,
    weight_customer_priority FLOAT DEFAULT 0.25,
    weight_material_availability FLOAT DEFAULT 0.20,
    weight_aging FLOAT DEFAULT 0.10,
    weight_slack FLOAT DEFAULT 0.05,
    
    -- Reglas de Secuenciación
    minimize_setups BOOLEAN DEFAULT TRUE,
    setup_weight FLOAT DEFAULT 1.0,
    sequence_by_color BOOLEAN DEFAULT TRUE,
    sequence_by_material BOOLEAN DEFAULT TRUE,
    sequence_by_width BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    max_wip_per_resource INTEGER DEFAULT 5,
    min_batch_size_pct FLOAT DEFAULT 0.1, -- % de capacidad turno
    allow_split_orders BOOLEAN DEFAULT TRUE,
    max_tardiness_days INTEGER DEFAULT 7,
    
    -- Material
    material_look_ahead_days INTEGER DEFAULT 3,
    enforce_material_availability BOOLEAN DEFAULT TRUE,
    
    -- Performance
    max_iterations INTEGER DEFAULT 1000,
    optimization_timeout_seconds INTEGER DEFAULT 300,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Constraints Específicas
CREATE TABLE constraints (
    id SERIAL PRIMARY KEY,
    constraint_type VARCHAR(50) NOT NULL, -- resource_unavailable, customer_blackout, material_critical, tooling_limited
    constraint_name VARCHAR(200),
    
    -- Aplicabilidad
    resource_id INTEGER REFERENCES resources(id),
    customer_id INTEGER REFERENCES customers(id),
    material_id INTEGER REFERENCES materials(id),
    order_id INTEGER REFERENCES orders(id),
    
    -- Vigencia
    effective_from DATE,
    effective_to DATE,
    
    -- Detalles
    constraint_details JSON,
    severity VARCHAR(20) DEFAULT 'hard', -- hard, soft
    penalty_weight FLOAT DEFAULT 1000, -- peso para soft constraints
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_constraints_type_active ON constraints(constraint_type, is_active);
CREATE INDEX idx_constraints_dates ON constraints(effective_from, effective_to, is_active);
```

### 2.6 Modificaciones a Tablas Existentes

```sql
-- Agregar a Order
ALTER TABLE orders ADD COLUMN abc_classification VARCHAR(10); -- A, B, C
ALTER TABLE orders ADD COLUMN customer_priority_override INTEGER;
ALTER TABLE orders ADD COLUMN material_ready BOOLEAN DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN tooling_ready BOOLEAN DEFAULT FALSE;
ALTER TABLE orders ADD COLUMN planning_slack_days INTEGER; -- holgura
ALTER TABLE orders ADD COLUMN aging_days INTEGER; -- días desde creación
ALTER TABLE orders ADD COLUMN current_mps_plan_id INTEGER REFERENCES mps_plans(id);

-- Agregar a OrderItem
ALTER TABLE order_items ADD COLUMN routing_id INTEGER REFERENCES routings(id);
ALTER TABLE order_items ADD COLUMN requires_setup BOOLEAN DEFAULT TRUE;
ALTER TABLE order_items ADD COLUMN setup_attributes JSON; -- {color, material, width, tooling}
ALTER TABLE order_items ADD COLUMN estimated_setup_minutes FLOAT;
ALTER TABLE order_items ADD COLUMN estimated_run_minutes FLOAT;
ALTER TABLE order_items ADD COLUMN material_requirements JSON; -- BOM simplificado

-- Agregar a Customer
ALTER TABLE customers ADD COLUMN abc_classification VARCHAR(10);
ALTER TABLE customers ADD COLUMN blackout_dates JSON; -- fechas no permitidas
ALTER TABLE customers ADD COLUMN preferred_resources JSON; -- recursos preferidos

-- Agregar a Material
ALTER TABLE materials ADD COLUMN is_critical BOOLEAN DEFAULT FALSE;
ALTER TABLE materials ADD COLUMN allocated_quantity FLOAT DEFAULT 0;
```

### 2.7 Índices Adicionales para Performance

```sql
-- Order queries
CREATE INDEX idx_orders_backorder_priority ON orders(is_backorder, priority, promised_date) WHERE is_backorder = TRUE;
CREATE INDEX idx_orders_material_ready ON orders(material_ready, tooling_ready, promised_date);
CREATE INDEX idx_orders_abc_priority ON orders(abc_classification, priority);

-- OrderItem queries
CREATE INDEX idx_order_items_routing ON order_items(routing_id, status);
CREATE INDEX idx_order_items_material_req ON order_items USING gin(material_requirements);

-- Material queries
CREATE INDEX idx_materials_critical_avail ON materials(is_critical, quantity_available) WHERE is_critical = TRUE;
CREATE INDEX idx_materials_allocated ON materials(material_code, allocated_quantity);
```

## 3. Algoritmo de Planificación MPS

### 3.1 Overview del Algoritmo

El algoritmo MPS implementa un enfoque de **planificación heurística en múltiples pasadas** con priorización multi-criterio y finite capacity scheduling:

1. **Preparación:** Cargar órdenes, capacidad, WIP, materiales
2. **Filtrado:** Separar órdenes listas vs bloqueadas
3. **Priorización:** Calcular score compuesto para cada orden
4. **Programación:** Asignar órdenes a recursos respetando capacidad
5. **Secuenciación:** Optimizar secuencia dentro de turno (minimizar setups)
6. **Validación:** Verificar factibilidad (material, capacidad, constraints)
7. **Optimización:** Mejoras locales (swap, move)
8. **Publicación:** Persistir plan y generar KPIs

### 3.2 Pseudo-código del Algoritmo Principal

```python
def run_mps_planning(horizon_start, horizon_end, parameters):
    """
    Algoritmo principal de planificación MPS
    """
    # 1. PREPARACIÓN
    plan = create_new_plan(horizon_start, horizon_end, parameters)
    orders = load_demand(horizon_start, horizon_end)
    resources = load_resources()
    capacity_calendar = build_capacity_calendar(resources, horizon_start, horizon_end)
    wip_state = load_current_wip()
    materials = load_material_inventory()
    setup_matrix = load_setup_times()
    
    # 2. FILTRADO Y CLASIFICACIÓN
    ready_orders = []
    blocked_orders = []
    
    for order in orders:
        material_ok = check_material_availability(order, materials, horizon_start)
        tooling_ok = check_tooling_availability(order, resources)
        constraint_ok = check_constraints(order, parameters)
        
        if material_ok and tooling_ok and constraint_ok:
            ready_orders.append(order)
        else:
            blocked_orders.append({
                'order': order,
                'blocking_reason': get_blocking_reason(material_ok, tooling_ok, constraint_ok)
            })
    
    # 3. PRIORIZACIÓN MULTI-CRITERIO
    prioritized_orders = calculate_priority_scores(ready_orders, parameters, wip_state)
    # Score = w1*due_date_score + w2*customer_score + w3*material_score + w4*aging_score + w5*slack_score
    prioritized_orders.sort(key=lambda x: x.total_score, reverse=True)
    
    # 4. PROGRAMACIÓN CON CAPACIDAD FINITA
    for order in prioritized_orders:
        routing = get_routing(order.item_code)
        
        for operation in routing.operations:
            # Encontrar recurso y slot disponible
            eligible_resources = find_eligible_resources(operation, resources)
            
            best_slot = None
            best_resource = None
            min_tardiness = float('inf')
            
            for resource in eligible_resources:
                # Buscar primer slot disponible con suficiente capacidad
                slot = find_first_available_slot(
                    resource, 
                    capacity_calendar, 
                    operation.required_capacity,
                    order.promised_date,
                    parameters
                )
                
                if slot:
                    tardiness = calculate_tardiness(slot.end_time, order.promised_date)
                    if tardiness < min_tardiness:
                        best_slot = slot
                        best_resource = resource
                        min_tardiness = tardiness
            
            if best_slot:
                # Asignar a plan
                plan_item = create_plan_item(
                    plan_id=plan.id,
                    order=order,
                    operation=operation,
                    resource=best_resource,
                    slot=best_slot,
                    setup_time=estimate_setup_time(best_resource, order, setup_matrix)
                )
                
                # Actualizar capacidad disponible
                capacity_calendar.consume(best_resource, best_slot, plan_item.duration)
                
                # Reservar materiales
                allocate_materials(plan_item, materials, order.material_requirements)
                
            else:
                # No hay capacidad disponible
                log_planning_exception(order, "insufficient_capacity", operation)
    
    # 5. SECUENCIACIÓN DENTRO DE TURNO (minimizar setups)
    for resource in resources:
        for date, shift in capacity_calendar.get_all_slots(resource):
            plan_items_in_slot = get_plan_items(plan, resource, date, shift)
            
            if len(plan_items_in_slot) > 1:
                # Optimizar secuencia usando TSP-like heuristic
                optimized_sequence = optimize_sequence(
                    plan_items_in_slot, 
                    setup_matrix, 
                    parameters
                )
                
                # Actualizar secuencias
                for idx, item in enumerate(optimized_sequence):
                    item.sequence_in_shift = (idx + 1) * 10  # 10, 20, 30...
                    update_plan_item_times(item, idx, setup_matrix)
    
    # 6. VALIDACIÓN Y FACTIBILIDAD
    violations = validate_plan(plan, parameters)
    plan.feasibility_score = calculate_feasibility(violations)
    plan.constraint_violations = violations
    
    # 7. OPTIMIZACIÓN LOCAL (opcional)
    if parameters.enable_local_optimization:
        improved_plan = local_search_optimization(
            plan, 
            parameters.max_iterations,
            parameters.optimization_timeout
        )
        if improved_plan.objective_value < plan.objective_value:
            plan = improved_plan
    
    # 8. CALCULAR KPIs
    plan.kpis = calculate_plan_kpis(plan, orders, blocked_orders)
    
    # 9. PERSISTIR Y AUDIT
    save_plan(plan)
    log_planning_decision_audit(plan, parameters, violations)
    
    return {
        'plan_id': plan.id,
        'scheduled_orders': len(prioritized_orders),
        'blocked_orders': len(blocked_orders),
        'feasibility_score': plan.feasibility_score,
        'kpis': plan.kpis,
        'violations': violations
    }
```

### 3.3 Funciones de Priorización Detalladas

```python
def calculate_priority_scores(orders, parameters, wip_state):
    """
    Calcular score compuesto de priorización para cada orden
    """
    scored_orders = []
    
    for order in orders:
        score = PriorityScore()
        
        # 1. Due Date Score (0-100)
        days_until_due = (order.promised_date - date.today()).days
        if days_until_due < 0:
            score.due_date = 100  # Overdue
        elif days_until_due == 0:
            score.due_date = 95
        elif days_until_due <= 2:
            score.due_date = 90
        elif days_until_due <= 7:
            score.due_date = 70
        elif days_until_due <= 14:
            score.due_date = 50
        else:
            score.due_date = max(0, 100 - days_until_due * 2)
        
        # 2. Customer Priority Score (0-100)
        if order.customer.abc_classification == 'A':
            score.customer = 100
        elif order.customer.abc_classification == 'B':
            score.customer = 70
        elif order.customer.abc_classification == 'C':
            score.customer = 40
        else:
            score.customer = 50
        
        # Ajustar por priority_level del customer
        score.customer = score.customer * (1.0 + (4 - order.customer.priority_level) * 0.1)
        score.customer = min(100, score.customer)
        
        # 3. Material Availability Score (0-100)
        material_avail_ratio = calculate_material_coverage(order, materials)
        score.material = material_avail_ratio * 100
        
        # 4. Aging Score (0-100) - cuánto tiempo lleva esperando
        score.aging = min(100, (order.aging_days / 30.0) * 100)
        
        # 5. Slack Score (0-100) - holgura de tiempo
        slack_ratio = order.planning_slack_days / max(1, days_until_due)
        score.slack = max(0, 100 - (slack_ratio * 100))
        
        # 6. WIP Urgency (bonus) - si ya está en proceso
        if order.id in wip_state and wip_state[order.id].status == 'in_progress':
            score.wip_bonus = 20
        else:
            score.wip_bonus = 0
        
        # Calcular score total ponderado
        score.total_score = (
            parameters.weight_due_date * score.due_date +
            parameters.weight_customer_priority * score.customer +
            parameters.weight_material_availability * score.material +
            parameters.weight_aging * score.aging +
            parameters.weight_slack * score.slack +
            score.wip_bonus
        )
        
        # Metadata para explicabilidad
        score.explanation = generate_priority_explanation(score, order)
        
        scored_orders.append({
            'order': order,
            'score': score
        })
    
    return scored_orders


def calculate_material_coverage(order, materials):
    """
    Calcula % de materiales disponibles para una orden
    """
    if not order.material_requirements:
        return 1.0
    
    total_items = len(order.material_requirements)
    available_items = 0
    
    for req in order.material_requirements:
        material = materials.get(req['material_code'])
        if material:
            available = material.quantity_available - material.allocated_quantity
            required = req['quantity_required']
            
            if available >= required:
                available_items += 1
            elif available >= required * 0.9:  # 90% coverage
                available_items += 0.9
    
    return available_items / total_items if total_items > 0 else 1.0
```

### 3.4 Algoritmo de Secuenciación (Minimize Setups)

```python
def optimize_sequence(plan_items, setup_matrix, parameters):
    """
    Optimizar secuencia de OT en un turno para minimizar setups
    Usa greedy nearest-neighbor heuristic (similar a TSP)
    """
    if len(plan_items) <= 1:
        return plan_items
    
    if not parameters.minimize_setups:
        return plan_items  # mantener orden de prioridad
    
    # Ordenar por atributo principal (ej. color)
    primary_attr = 'color' if parameters.sequence_by_color else 'material'
    
    sequenced = []
    remaining = list(plan_items)
    
    # Empezar con item de mayor prioridad
    current = remaining.pop(0)
    sequenced.append(current)
    
    while remaining:
        current_attrs = current.order_item.setup_attributes
        
        min_setup_time = float('inf')
        best_next = None
        best_idx = -1
        
        # Encontrar siguiente item con mínimo setup
        for idx, candidate in enumerate(remaining):
            candidate_attrs = candidate.order_item.setup_attributes
            
            setup_time = calculate_setup_time(
                current_attrs, 
                candidate_attrs, 
                current.resource_id, 
                setup_matrix
            )
            
            # Penalizar si rompe el flujo de color/material
            if parameters.sequence_by_color:
                if current_attrs.get('color') != candidate_attrs.get('color'):
                    setup_time *= 1.5
            
            if setup_time < min_setup_time:
                min_setup_time = setup_time
                best_next = candidate
                best_idx = idx
        
        if best_next:
            sequenced.append(best_next)
            remaining.pop(best_idx)
            current = best_next
    
    return sequenced


def calculate_setup_time(from_attrs, to_attrs, resource_id, setup_matrix):
    """
    Calcular tiempo de setup entre dos items
    """
    total_setup = 0
    
    # Tiempo base de setup
    base_setup = 15  # minutos default
    
    # Buscar en matriz de setup por cada atributo
    for attr_type in ['color', 'material', 'width', 'tooling']:
        from_val = from_attrs.get(attr_type)
        to_val = to_attrs.get(attr_type)
        
        if from_val and to_val and from_val != to_val:
            # Buscar en setup_times table
            setup_record = setup_matrix.get(
                (resource_id, attr_type, from_val, to_val)
            )
            
            if setup_record:
                total_setup += setup_record.setup_time_minutes
            else:
                # Default por tipo
                if attr_type == 'color':
                    total_setup += 30
                elif attr_type == 'material':
                    total_setup += 45
                elif attr_type == 'tooling':
                    total_setup += 60
                else:
                    total_setup += 20
    
    return max(base_setup, total_setup)
```

### 3.5 Ubicación del Código

**Archivo principal:** `backend/app/services/mps_service.py`

**Módulos complementarios:**
- `backend/app/services/mps_algorithms.py` - Algoritmos de optimización
- `backend/app/services/mps_prioritization.py` - Lógica de priorización
- `backend/app/services/mps_sequencing.py` - Secuenciación y setups
- `backend/app/services/mps_validation.py` - Validaciones y constraints
- `backend/app/services/mps_kpi_calculator.py` - Cálculo de KPIs

(Continúa en siguiente sección...)
