# Diseño MPS - Parte 3: APIs y UI

## 5. APIs del MPS

### 5.1 Endpoints REST

#### 5.1.1 POST /api/mps/run - Ejecutar Planificación

**Descripción:** Ejecuta el algoritmo de planificación MPS con parámetros configurables.

**Request:**
```json
{
    "horizon_start_date": "2024-02-01",
    "horizon_end_date": "2024-03-15",
    "bucket_type": "shift",
    "parameter_set_id": 1,
    "custom_parameters": {
        "weight_due_date": 0.45,
        "weight_customer_priority": 0.30,
        "minimize_setups": true,
        "max_tardiness_days": 5
    },
    "mode": "full",
    "filters": {
        "include_customers": ["CUST001", "CUST002"],
        "exclude_orders": [],
        "min_priority": 2
    }
}
```

**Response:**
```json
{
    "status": "success",
    "plan_id": 42,
    "execution_time_seconds": 12.5,
    "summary": {
        "total_orders_evaluated": 156,
        "orders_scheduled": 142,
        "orders_blocked": 14,
        "utilization_avg": 0.82,
        "feasibility_score": 0.95
    },
    "kpis": {
        "otif_projected": 0.89,
        "total_tardiness_days": 23,
        "throughput_avg": 12500,
        "setup_time_ratio": 0.13
    },
    "violations": [
        {
            "type": "capacity_overload",
            "resource_id": 3,
            "date": "2024-02-15",
            "shift": "Turno 1",
            "severity": "high"
        }
    ],
    "blocked_orders": [
        {
            "order_number": "ORD-12345",
            "reason": "material_shortage",
            "blocking_materials": ["PAPEL-TERM-80"],
            "expected_available_date": "2024-02-10"
        }
    ]
}
```

**Implementación:**
```python
# backend/app/routes/mps.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.services.mps_service import MPSService
from app.models import MPSPlan, PlanningParameter, User, AuditLog
from datetime import datetime
import logging

bp = Blueprint('mps', __name__)
logger = logging.getLogger(__name__)


@bp.route('/run', methods=['POST'])
@jwt_required()
def run_mps_planning():
    """Ejecutar planificación MPS"""
    user_identity = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        # Validar parámetros
        if not data.get('horizon_start_date') or not data.get('horizon_end_date'):
            return jsonify({'error': 'Missing required date parameters'}), 400
        
        horizon_start = datetime.fromisoformat(data['horizon_start_date'])
        horizon_end = datetime.fromisoformat(data['horizon_end_date'])
        
        # Cargar parámetros
        param_set_id = data.get('parameter_set_id')
        if param_set_id:
            params = PlanningParameter.query.get(param_set_id)
            if not params:
                return jsonify({'error': 'Parameter set not found'}), 404
        else:
            # Usar parámetros por defecto
            params = PlanningParameter.query.filter_by(is_active=True).first()
            if not params:
                return jsonify({'error': 'No active parameter set found'}), 400
        
        # Merge custom parameters
        if data.get('custom_parameters'):
            params = merge_parameters(params, data['custom_parameters'])
        
        # Ejecutar planificación
        mps_service = MPSService()
        result = mps_service.run_planning(
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            parameters=params,
            mode=data.get('mode', 'full'),
            filters=data.get('filters', {})
        )
        
        # Audit log
        log_planning_execution(user_identity, result['plan_id'], data)
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in MPS planning: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in MPS planning: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


def log_planning_execution(user_identity, plan_id, request_data):
    """Log planning execution for audit"""
    audit = AuditLog(
        user_id=get_user_id(user_identity),
        action='mps_planning_executed',
        entity='mps_plan',
        entity_id=str(plan_id),
        details={
            'horizon_start': request_data.get('horizon_start_date'),
            'horizon_end': request_data.get('horizon_end_date'),
            'parameter_set_id': request_data.get('parameter_set_id'),
            'mode': request_data.get('mode')
        }
    )
    db.session.add(audit)
    db.session.commit()
```

#### 5.1.2 GET /api/mps/plan - Obtener Plan

**Descripción:** Recupera el plan MPS con filtros.

**Query Parameters:**
- `plan_id`: ID del plan (default: plan activo)
- `resource_id`: Filtrar por recurso
- `date_from`, `date_to`: Rango de fechas
- `customer_id`: Filtrar por cliente
- `status`: Estado de items (planned, locked, in_progress, completed)
- `include_kpis`: Incluir KPIs calculados (true/false)

**Response:**
```json
{
    "plan": {
        "id": 42,
        "plan_name": "Plan Semanal 2024-W05",
        "plan_version": 1,
        "plan_status": "active",
        "horizon_start_date": "2024-02-01",
        "horizon_end_date": "2024-03-15",
        "bucket_type": "shift",
        "feasibility_score": 0.95,
        "created_at": "2024-01-30T10:30:00Z",
        "created_by": "admin"
    },
    "plan_items": [
        {
            "id": 1001,
            "order_number": "ORD-12345",
            "order_item_id": 5001,
            "customer_name": "Cliente ABC",
            "item_code": "ETQ-001",
            "item_description": "Etiqueta térmica azul 80mm",
            "resource": {
                "id": 3,
                "code": "PRESS-01",
                "name": "Prensa 1"
            },
            "scheduled_date": "2024-02-05",
            "scheduled_shift": "Turno 1",
            "sequence_in_shift": 10,
            "start_time": "2024-02-05T06:00:00Z",
            "end_time": "2024-02-05T09:30:00Z",
            "setup_time_minutes": 30,
            "run_time_minutes": 180,
            "planned_quantity": 5000,
            "planned_unit": "metros",
            "status": "planned",
            "is_locked": false,
            "material_allocated": true,
            "priority": 1,
            "planning_notes": "Scheduled early due to high customer priority and tight due date"
        }
    ],
    "kpis": {
        "otif_projected": 0.89,
        "total_tardiness_days": 23,
        "avg_resource_utilization": 0.82,
        "setup_time_ratio": 0.13,
        "material_availability": 0.94
    },
    "pagination": {
        "page": 1,
        "per_page": 50,
        "total": 142,
        "pages": 3
    }
}
```

**Implementación:**
```python
@bp.route('/plan', methods=['GET'])
@jwt_required()
def get_mps_plan():
    """Obtener plan MPS con filtros"""
    try:
        # Parámetros
        plan_id = request.args.get('plan_id', type=int)
        resource_id = request.args.get('resource_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer_id = request.args.get('customer_id', type=int)
        status = request.args.get('status')
        include_kpis = request.args.get('include_kpis', 'true').lower() == 'true'
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Obtener plan
        if plan_id:
            plan = MPSPlan.query.get(plan_id)
        else:
            # Plan activo
            plan = MPSPlan.query.filter_by(plan_status='active').first()
        
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        # Query plan items con filtros
        query = MPSPlanItem.query.filter_by(mps_plan_id=plan.id)
        
        if resource_id:
            query = query.filter_by(resource_id=resource_id)
        
        if date_from:
            query = query.filter(MPSPlanItem.scheduled_date >= datetime.fromisoformat(date_from))
        
        if date_to:
            query = query.filter(MPSPlanItem.scheduled_date <= datetime.fromisoformat(date_to))
        
        if customer_id:
            query = query.join(Order).filter(Order.customer_id == customer_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar
        query = query.order_by(
            MPSPlanItem.scheduled_date,
            MPSPlanItem.resource_id,
            MPSPlanItem.sequence_in_shift
        )
        
        # Paginar
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Serializar
        plan_items = [item.to_dict() for item in paginated.items]
        
        result = {
            'plan': plan.to_dict(),
            'plan_items': plan_items,
            'pagination': {
                'page': paginated.page,
                'per_page': paginated.per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        }
        
        # KPIs
        if include_kpis:
            from app.services.mps_kpi_calculator import MPSKPICalculator
            kpi_calc = MPSKPICalculator()
            result['kpis'] = kpi_calc.calculate_plan_kpis(plan)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error retrieving MPS plan: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

#### 5.1.3 PUT /api/mps/override - Manual Override

**Descripción:** Permite bloquear/forzar asignaciones manualmente.

**Request:**
```json
{
    "plan_item_id": 1001,
    "action": "lock",
    "override_data": {
        "is_locked": true,
        "locked_reason": "Cliente VIP requiere esta fecha específica",
        "priority_override": 1
    }
}
```

o

```json
{
    "plan_item_id": 1002,
    "action": "move",
    "override_data": {
        "new_resource_id": 5,
        "new_scheduled_date": "2024-02-08",
        "new_scheduled_shift": "Turno 2",
        "reason": "Mantenimiento programado en recurso original"
    }
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Plan item locked successfully",
    "plan_item": {
        "id": 1001,
        "is_locked": true,
        "locked_by": "admin",
        "locked_at": "2024-01-30T14:25:00Z"
    },
    "warnings": [
        "Locking this item may impact subsequent items in sequence"
    ]
}
```

**Implementación:**
```python
@bp.route('/override', methods=['PUT'])
@jwt_required()
def override_plan_item():
    """Override manual de plan item"""
    user_identity = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        plan_item_id = data.get('plan_item_id')
        action = data.get('action')  # lock, unlock, move, delete
        
        if not plan_item_id or not action:
            return jsonify({'error': 'Missing required fields'}), 400
        
        plan_item = MPSPlanItem.query.get(plan_item_id)
        if not plan_item:
            return jsonify({'error': 'Plan item not found'}), 404
        
        # Verificar que el plan no esté archived
        if plan_item.mps_plan.plan_status == 'archived':
            return jsonify({'error': 'Cannot modify archived plan'}), 400
        
        override_data = data.get('override_data', {})
        warnings = []
        
        if action == 'lock':
            plan_item.is_locked = True
            plan_item.planning_notes = override_data.get('locked_reason', 'Locked by user')
            
            if override_data.get('priority_override'):
                plan_item.priority_override = override_data['priority_override']
            
            warnings.append("Replanning will skip this locked item")
        
        elif action == 'unlock':
            plan_item.is_locked = False
            plan_item.priority_override = None
        
        elif action == 'move':
            # Mover a nuevo recurso/fecha/turno
            new_resource_id = override_data.get('new_resource_id')
            new_date = override_data.get('new_scheduled_date')
            new_shift = override_data.get('new_scheduled_shift')
            
            if new_resource_id:
                plan_item.resource_id = new_resource_id
            if new_date:
                plan_item.scheduled_date = datetime.fromisoformat(new_date)
            if new_shift:
                plan_item.scheduled_shift = new_shift
            
            # Recalcular tiempos
            plan_item.sequence_in_shift = 999  # al final del turno
            
            plan_item.planning_notes = f"Moved manually: {override_data.get('reason', 'No reason provided')}"
            plan_item.is_locked = True  # Auto-lock al mover
            
            warnings.append("Item moved and auto-locked to prevent replanning")
        
        elif action == 'delete':
            # Eliminar del plan
            db.session.delete(plan_item)
            
            # Audit log
            log_plan_item_deletion(user_identity, plan_item, override_data.get('reason'))
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Plan item deleted'
            }), 200
        
        else:
            return jsonify({'error': f'Invalid action: {action}'}), 400
        
        db.session.commit()
        
        # Audit log
        log_plan_override(user_identity, plan_item, action, override_data)
        
        return jsonify({
            'status': 'success',
            'message': f'Plan item {action}ed successfully',
            'plan_item': plan_item.to_dict(),
            'warnings': warnings
        }), 200
        
    except Exception as e:
        logger.error(f"Error in plan override: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
```

#### 5.1.4 GET /api/wip - Estado WIP Real-Time

**Response:**
```json
{
    "wip_states": [
        {
            "order_number": "ORD-12345",
            "order_item_id": 5001,
            "item_code": "ETQ-001",
            "current_operation": 10,
            "current_resource": {
                "id": 3,
                "code": "PRESS-01",
                "name": "Prensa 1"
            },
            "status": "in_progress",
            "quantity_completed": 2500,
            "quantity_planned": 5000,
            "completion_percentage": 50,
            "actual_start_time": "2024-02-05T06:15:00Z",
            "estimated_completion_time": "2024-02-05T09:30:00Z",
            "operator": "Juan Perez",
            "has_exception": false
        },
        {
            "order_number": "ORD-12346",
            "order_item_id": 5002,
            "item_code": "ETQ-002",
            "current_operation": 20,
            "current_resource": {
                "id": 5,
                "code": "LAMINATOR-01",
                "name": "Laminadora 1"
            },
            "status": "on_hold",
            "quantity_completed": 1000,
            "quantity_planned": 3000,
            "completion_percentage": 33,
            "actual_start_time": "2024-02-05T08:00:00Z",
            "has_exception": true,
            "exception_type": "material_shortage",
            "exception_details": "Falta adhesivo especial para laminado"
        }
    ],
    "summary": {
        "total_wip": 15,
        "in_progress": 12,
        "on_hold": 3,
        "total_exceptions": 3
    },
    "last_updated": "2024-02-05T10:45:00Z"
}
```

#### 5.1.5 GET /api/mps/kpis - KPIs Dashboard

**Response:**
```json
{
    "period": {
        "start_date": "2024-02-01",
        "end_date": "2024-03-15"
    },
    "kpis": {
        "otif": {
            "value": 0.89,
            "target": 0.95,
            "status": "warning",
            "trend": "improving",
            "details": {
                "on_time": 124,
                "late": 18,
                "total": 142
            }
        },
        "tardiness": {
            "total_days": 23,
            "avg_per_order": 0.16,
            "target_total_days": 20,
            "status": "warning",
            "worst_offenders": [
                {"order_number": "ORD-12350", "days_late": 5},
                {"order_number": "ORD-12355", "days_late": 4}
            ]
        },
        "throughput": {
            "value": 12500,
            "unit": "metros/turno",
            "target": 13000,
            "utilization": 0.82,
            "status": "good"
        },
        "setup_ratio": {
            "value": 0.13,
            "target": 0.15,
            "status": "good",
            "total_setup_hours": 156,
            "total_run_hours": 1044
        },
        "wip": {
            "current_wip": 15,
            "target_max": 20,
            "status": "good",
            "avg_wip": 12
        },
        "material_availability": {
            "value": 0.94,
            "target": 0.90,
            "status": "good",
            "shortages": 2,
            "critical_shortages": 0
        }
    },
    "charts": {
        "otif_trend": {
            "labels": ["W01", "W02", "W03", "W04", "W05"],
            "values": [0.87, 0.88, 0.89, 0.91, 0.89]
        },
        "resource_utilization": [
            {"resource": "PRESS-01", "utilization": 0.85},
            {"resource": "PRESS-02", "utilization": 0.78},
            {"resource": "LAMINATOR-01", "utilization": 0.82}
        ]
    }
}
```

#### 5.1.6 GET /api/mps/exceptions - Excepciones y Alertas

**Response:**
```json
{
    "exceptions": [
        {
            "type": "material_shortage",
            "severity": "high",
            "entity_type": "order",
            "entity_id": "ORD-12345",
            "resource_id": null,
            "date": "2024-02-08",
            "description": "Material PAPEL-TERM-80 insuficiente para completar orden",
            "impact": {
                "orders_affected": 3,
                "revenue_at_risk": 15000,
                "customer_priority": "A"
            },
            "recommended_action": "Expeditar orden de compra PO-2024-050",
            "status": "open",
            "created_at": "2024-02-05T09:00:00Z"
        },
        {
            "type": "capacity_overload",
            "severity": "medium",
            "entity_type": "resource",
            "entity_id": null,
            "resource_id": 3,
            "date": "2024-02-15",
            "shift": "Turno 1",
            "description": "Recurso PRESS-01 sobrecargado en Turno 1",
            "impact": {
                "overload_percentage": 115,
                "orders_affected": 2
            },
            "recommended_action": "Redistribuir a PRESS-02 o agregar Turno 4",
            "status": "open"
        },
        {
            "type": "tardiness_risk",
            "severity": "high",
            "entity_type": "order",
            "entity_id": "ORD-12360",
            "description": "Orden en riesgo de entrega tardía (5 días)",
            "impact": {
                "customer": "Cliente VIP",
                "customer_priority": "A",
                "days_late": 5
            },
            "recommended_action": "Evaluar priorización urgente o comunicar a cliente",
            "status": "open"
        }
    ],
    "summary": {
        "total_exceptions": 15,
        "by_severity": {
            "critical": 2,
            "high": 5,
            "medium": 6,
            "low": 2
        },
        "by_type": {
            "material_shortage": 4,
            "capacity_overload": 3,
            "tardiness_risk": 5,
            "tooling_unavailable": 2,
            "quality_issue": 1
        }
    }
}
```

## 6. UI/Frontend para MPS

### 6.1 Pantallas Propuestas

#### 6.1.1 Gantt Chart por Recurso/Turno

**Componente:** `frontend/src/pages/MPSGanttView.jsx`

**Características:**
- Vista tipo Gantt horizontal con recursos en eje Y y tiempo en eje X
- Buckets configurables (turno, día, semana)
- Barras coloreadas por:
  - Prioridad (rojo=urgente, amarillo=alta, verde=normal)
  - Estado (gris=planned, azul=in_progress, verde=completed)
  - Cliente (colores por clasificación ABC)
- Drag-and-drop para mover items (llama a PUT /api/mps/override)
- Click en barra muestra detalle de orden
- Indicadores visuales:
  - Setup times (barras ralladas)
  - Locked items (candado)
  - Overload (fondo rojo)
  - Material faltante (ícono de alerta)

**Tecnología:** Recharts o react-gantt-chart library

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  MPS Gantt View                    [Filtros] [Hoy] [Zoom]   │
├──────────┬──────────────────────────────────────────────────┤
│Resource  │  Feb 05    │  Feb 06    │  Feb 07    │  Feb 08  │
│          │ T1 T2 T3   │ T1 T2 T3   │ T1 T2 T3   │ T1 T2 T3 │
├──────────┼──────────────────────────────────────────────────┤
│PRESS-01  │[=====]     │[====] [==] │            │[========]│
│  85% util│  OT-123    │ OT-124 125 │            │ OT-130   │
├──────────┼──────────────────────────────────────────────────┤
│PRESS-02  │      [====]│[=========] │[===] ⚠️    │          │
│  78% util│      OT-126│   OT-127   │OT-128      │          │
├──────────┼──────────────────────────────────────────────────┤
│LAMINA-01 │            │      [====]│[==========]│[====]    │
│  82% util│            │      OT-140│   OT-141   │OT-142    │
└──────────┴──────────────────────────────────────────────────┘

Legend: [====] Normal   [////] Setup   🔒 Locked   ⚠️ Material issue
```

#### 6.1.2 Backlog Priorizado con Ready/Not Ready

**Componente:** `frontend/src/pages/MPSBacklogView.jsx`

**Características:**
- Lista de órdenes con score de prioridad
- Badges indicando ready/not-ready
- Filtros por:
  - Material ready (verde/rojo)
  - Tooling ready (verde/rojo)
  - Customer priority (A/B/C)
  - Due date range
- Acciones:
  - Ver detalles
  - Force scheduling (override)
  - Marcar como bloqueada
- Sort by: Priority score, Due date, Aging

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  MPS Backlog - Órdenes Pendientes                           │
│  [Filtros: Material ✓] [Tooling ✓] [Customer: Todos ▾]     │
├──────────┬────────────┬───────┬──────────┬─────────┬────────┤
│Order     │Customer    │Score  │Due Date  │Ready    │Actions │
├──────────┼────────────┼───────┼──────────┼─────────┼────────┤
│ORD-12345 │Cliente ABC │ 95.2  │Feb 08    │✓ Mat    │[View]  │
│Priority 1│Class A     │       │(3 días)  │✓ Tool   │[Force] │
│ETQ-001   │            │       │          │✓ Sched  │        │
├──────────┼────────────┼───────┼──────────┼─────────┼────────┤
│ORD-12346 │Cliente XYZ │ 87.5  │Feb 10    │✓ Mat    │[View]  │
│Priority 2│Class B     │       │(5 días)  │✗ Tool   │[Block] │
│ETQ-002   │            │       │          │❓Pend   │        │
├──────────┼────────────┼───────┼──────────┼─────────┼────────┤
│ORD-12350 │Cliente VIP │ 92.0  │Feb 06    │✗ Mat    │[View]  │
│Priority 1│Class A     │       │(1 día!)  │✓ Tool   │[Alert] │
│ETQ-005   │            │       │          │✗ Block  │        │
└──────────┴────────────┴───────┴──────────┴─────────┴────────┘

Total: 156 orders | Scheduled: 142 | Blocked: 14 | Ready: 135
```

#### 6.1.3 Panel de Excepciones

**Componente:** `frontend/src/pages/MPSExceptionsView.jsx`

**Características:**
- Dashboard de alertas categorizadas
- Filtros por severity (critical, high, medium, low)
- Filtros por tipo (shortage, overload, tardiness, quality)
- Acciones sugeridas por excepción
- Ack/resolve exceptions

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  MPS Exceptions Dashboard                 🔴 15 Open        │
│  [Critical: 2] [High: 5] [Medium: 6] [Low: 2]              │
├─────────────────────────────────────────────────────────────┤
│ 🔴 CRITICAL - Material Shortage                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ PAPEL-TERM-80 shortage                                  │ │
│ │ Impact: 3 orders, $15K revenue, Customer Class A       │ │
│ │ Recommended: Expedite PO-2024-050                       │ │
│ │ [Ack] [Resolve] [Details]                               │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🟠 HIGH - Tardiness Risk                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ORD-12360 at risk (5 days late)                         │ │
│ │ Customer: Cliente VIP (Class A)                         │ │
│ │ Recommended: Prioritize or notify customer              │ │
│ │ [Reprioritize] [Notify] [Details]                       │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ 🟡 MEDIUM - Capacity Overload                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ PRESS-01 overloaded Feb 15 Shift 1 (115%)              │ │
│ │ Recommended: Redistribute to PRESS-02                   │ │
│ │ [Redistribute] [Details]                                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 6.1.4 KPI Dashboard MPS

**Componente:** `frontend/src/pages/MPSKPIDashboard.jsx`

**Características:**
- Cards con KPIs principales
- Gráficas de tendencia (Recharts)
- Comparación vs targets
- Drill-down a detalles

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  MPS KPI Dashboard - Week 05 2024                           │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ OTIF        │ Tardiness   │ Throughput  │ Setup Ratio    │
│ 89%         │ 23 days     │ 12.5K m/turn│ 13%            │
│ Target: 95% │ Target: 20  │ Target: 13K │ Target: <15%   │
│ 🟡 Warning  │ 🟡 Warning  │ 🟢 Good     │ 🟢 Good        │
├─────────────┴─────────────┴─────────────┴─────────────────┤
│ OTIF Trend (Last 5 weeks)                                  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │     *                                                   ││
│ │    / \      *                                          ││
│ │   *   \    / \                                         ││
│ │        \  /   *                                        ││
│ │         *                                              ││
│ │ W01  W02  W03  W04  W05                                ││
│ └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│ Resource Utilization                                        │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ PRESS-01     ████████████████░░ 85%                    ││
│ │ PRESS-02     ██████████████░░░░ 78%                    ││
│ │ LAMINATOR-01 ████████████████░░ 82%                    ││
│ │ SLITTER-01   ████████████░░░░░░ 70%                    ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Estructura de Archivos Frontend

```
frontend/
├── src/
│   ├── pages/
│   │   ├── MPSGanttView.jsx          # Gantt chart
│   │   ├── MPSBacklogView.jsx        # Backlog priorizado
│   │   ├── MPSExceptionsView.jsx     # Excepciones
│   │   ├── MPSKPIDashboard.jsx       # KPIs
│   │   ├── MPSPlanningControl.jsx    # Control panel para ejecutar planning
│   │   └── MPSWIPMonitor.jsx         # Monitor de WIP real-time
│   ├── components/
│   │   ├── mps/
│   │   │   ├── GanttChart.jsx
│   │   │   ├── ResourceTimeline.jsx
│   │   │   ├── PriorityBadge.jsx
│   │   │   ├── ReadyStatusIndicator.jsx
│   │   │   ├── ExceptionCard.jsx
│   │   │   ├── KPICard.jsx
│   │   │   └── OverrideDialog.jsx
│   ├── services/
│   │   └── mpsApi.js                  # API client para MPS endpoints
│   └── hooks/
│       ├── useMPSPlan.js
│       ├── useMPSKPIs.js
│       └── useWIPState.js
```

(Continúa en DISEÑO_MPS_PARTE4.md...)
