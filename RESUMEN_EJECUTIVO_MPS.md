# Resumen Ejecutivo: Transformación MPS del Sistema Backorder-PCM

## Entregables Completados

Este documento resume la transformación del sistema Backorder-PCM para operar como un **Master Production Schedule (MPS)** real para una planta de etiquetas, integrando Syteline, Mongus e Intranet.

---

## 1. DOCUMENTACIÓN DE DISEÑO COMPLETA (4 Partes)

### DISEÑO_MPS.md - Fundamentos del Negocio
- **Definición del MPS para planta de etiquetas:**
  - Horizonte: 2-8 semanas (corto/mediano/largo plazo)
  - Bucket: Turno (3/día), Día, Semana
  - Unidades: OT, metros lineales, rollos, setups
  - KPIs: OTIF (>95%), Tardiness, Throughput, Setup Ratio, WIP, Material Availability

- **Modelo de datos completo (15+ tablas nuevas):**
  - `resources`, `shift_calendars`, `calendar_exceptions`
  - `routings`, `routing_operations`, `setup_times`
  - `mps_plans`, `mps_plan_items`
  - `wip_states`, `material_allocations`
  - `planning_parameters`, `constraints`, `sync_cursors`
  - Modificaciones a `orders`, `order_items`, `customers`, `materials`
  - Índices optimizados para performance

- **Algoritmo de planificación implementable:**
  - Preparación: Cargar demanda, capacidad, WIP, materiales
  - Filtrado: Órdenes ready vs blocked
  - Priorización multi-criterio (due date 40%, customer 25%, material 20%, aging 10%, slack 5%)
  - Programación finite capacity por recurso/turno
  - Secuenciación setup-aware (minimizar changeovers)
  - Validación de factibilidad
  - Optimización local opcional
  - Pseudo-código Python detallado

### DISEÑO_MPS_PARTE2.md - Integración y Sincronización
- **Datos a extraer por ERP:**
  - **Syteline:** Queries SQL para orders, WIP, inventory, BOM, routings, capacity
  - **Mongus:** Endpoints REST API para orders, WIP, inventory
  - **Intranet:** Endpoints custom para pedidos, producción

- **Estrategia de sync incremental:**
  - Modelo `sync_cursors` para tracking
  - Sync cada 5 minutos (órdenes, WIP, materiales)
  - Nightly reconciliation a las 2 AM
  - Upsert basado en `erp_source + erp_id`

- **Resolución de conflictos:**
  - **Fechas y cantidades:** ERP manda (source of truth)
  - **Prioridades y MPS assignments:** Local manda
  - **WIP estado:** ERP manda (tiempo real)
  - **Notas y overrides:** Local manda

- **Resilience patterns:**
  - Circuit breaker por cada ERP (failure threshold, timeout, half-open)
  - Retry con exponential backoff
  - Sistema sigue operando con datos locales si ERP cae

### DISEÑO_MPS_PARTE3.md - APIs y UI
- **7 Endpoints REST diseñados:**
  1. `POST /api/mps/run` - Ejecutar planificación (JSON request/response ejemplo)
  2. `GET /api/mps/plan` - Obtener plan con filtros (pagination, KPIs)
  3. `PUT /api/mps/override` - Lock/move items manualmente
  4. `GET /api/wip` - Estado real-time de WIP
  5. `GET /api/mps/kpis` - Dashboard de KPIs (OTIF, tardiness, throughput)
  6. `GET /api/mps/exceptions` - Alertas (shortages, overload, tardiness)
  7. `GET /api/mps/feasibility` - Validar factibilidad antes de scheduling

- **6 Pantallas UI propuestas:**
  1. **Gantt Chart** por recurso/turno (drag-and-drop, colores por prioridad)
  2. **Backlog Priorizado** con ready/not-ready indicators
  3. **Panel de Excepciones** (material shortage, capacity overload, tardiness risk)
  4. **KPI Dashboard** con trends y resource utilization
  5. **WIP Monitor** (plan vs actual, real-time)
  6. **Planning Control** panel para ejecutar planning con parámetros

- **Estructura de archivos frontend:**
  - Pages: `MPSGanttView.jsx`, `MPSBacklogView.jsx`, `MPSExceptionsView.jsx`, etc.
  - Components: `GanttChart.jsx`, `PriorityBadge.jsx`, `ReadyStatusIndicator.jsx`, etc.
  - Services: `mpsApi.js` (API client)
  - Hooks: `useMPSPlan.js`, `useMPSKPIs.js`, `useWIPState.js`

### DISEÑO_MPS_PARTE4.md - Implementación y Backlog
- **Metodología incremental en 7 fases:**
  - **Fase 1:** MPS bucket diario sin secuenciación fina (2-3 semanas)
  - **Fase 2:** Finite capacity + secuenciación simple (2-3 semanas)
  - **Fase 3:** Setups + tooling + optimización (3-4 semanas)
  - **Fase 4:** WIP integration + replanning incremental (2-3 semanas)
  - **Fase 5:** Material allocation + constraint validation (2 semanas)
  - **Fase 6:** Enhanced sync + circuit breaker (2 semanas)
  - **Fase 7:** Advanced UI + write-back opcional (3 semanas)

- **Cada fase incluye:**
  - Entregables específicos
  - Criterios de aceptación verificables
  - Pruebas mínimas

- **Backlog priorizado:**
  - **P0 (Crítico):** JWT identity bug, secrets en config, CSV security, Celery config
  - **P1 (Alta):** Modelos MPS core, MPSService básico, API routes, Frontend básico
  - **P2 (Media):** WIP models, Sync extensions, Setup times, Material allocations, KPI calculator

- **Estructura de archivos final:**
  - 40+ archivos a crear/modificar listados con rutas exactas

- **Configuración MPS en config.yaml:**
  - Horizonte, buckets, pesos, reglas de secuenciación, constraints, performance tuning

---

## 2. CORRECCIONES P0 IMPLEMENTADAS

### P0.1: JWT Identity Bug - COMPLETADO ✅
**Problema:** `get_jwt_identity()` retornaba inconsistentemente username o user_id

**Solución implementada:**
- Creado `backend/app/utils/auth_helpers.py` con:
  - `get_current_user_id()` - Maneja ambos casos (int o str)
  - `get_current_user()` - Retorna objeto User completo
  - `get_current_username()` - Retorna username
  - `require_role(roles)` - Decorator para verificar roles

- Actualizado `backend/app/routes/admin.py`:
  - Reemplazado `get_jwt_identity()` directo por `get_current_user()`
  - `admin_required` decorator usa helper
  - Audit logs usan `get_current_user_id()`

**Impacto:** JWT identity ahora es consistente en toda la app. Previene errores de autenticación.

### P0.2: Secrets en config.yaml - COMPLETADO ✅
**Problema:** Passwords y secrets hardcoded en `config.yaml`

**Solución implementada:**
- Creado `.env.example` con template de todas las variables
- Actualizado `backend/app/__init__.py`:
  - Función `load_config()` lee de config.yaml
  - Override con env vars: `SECRET_KEY`, `JWT_SECRET_KEY`, `DB_PASSWORD`, etc.
  - Soporte para todos los ERPs (Syteline, Mongus, Intranet)

- `.env` en `.gitignore` (ya existía)

**Uso:**
```bash
# Copiar template
cp .env.example .env

# Editar .env con valores reales
nano .env

# Docker compose auto-carga .env
docker-compose up
```

**Impacto:** Secrets ahora están fuera de git. Producción puede usar env vars sin modificar config.yaml.

### P0.3: CSV Upload Security - COMPLETADO ✅
**Problema:** CSV upload sin validación suficiente

**Solución implementada:**
- Creado `CSVImporterValidator` class en `csv_importer.py`:
  - `ALLOWED_EXTENSIONS = {'csv', 'txt'}`
  - `MAX_FILE_SIZE = 10MB`
  - `MAX_ROWS = 10000`
  - `validate_file(file)` - Valida extension antes de guardar
  - `validate_row_count(df)` - Valida número de filas
  - `sanitize_string(value, max_length)` - Remueve null bytes, caracteres control, trunca

- Actualizado `backend/app/routes/importer.py`:
  - Usa `secure_filename()` de werkzeug
  - Valida archivo antes de guardar
  - UUID en filename para evitar colisiones
  - Directorio temporal dedicado: `/tmp/backorder_uploads`
  - Valida tamaño después de guardar
  - Cleanup automático en finally block
  - Error handling completo con logs
  - Usa `get_current_user()` helper

- Actualizado `csv_importer.py`:
  - Todas las strings sanitizadas con `CSVImporterValidator.sanitize_string()`
  - Validación de row count
  - Error handling por fila con logging
  - Max length por campo (50-500 chars según campo)

**Impacto:** Previene inyección, DoS por archivos grandes, y errores por datos malformados.

### P0.4: Celery Configuration - COMPLETADO ✅
**Problema:** Celery mal configurado

**Solución implementada:**
- Creado `backend/celeryworker.py`:
  - Inicializa Flask app
  - Crea Celery app con `create_celery_app()`
  - Entry point para worker

- Actualizado `docker-compose.yml`:
  - Servicio `celery_worker` usa `python celeryworker.py worker --loglevel=info`
  - Mismo environment que backend
  - Acceso a logs y config.yaml

**Uso:**
```bash
# Docker compose
docker-compose up celery_worker

# Local
python backend/celeryworker.py worker --loglevel=info
```

**Impacto:** Celery worker ahora funciona correctamente. Listo para tareas async (sync ERP, planning, etc.).

---

## 3. DECISIONES ARQUITECTÓNICAS CLAVE

1. **Postgres como operational store:** Todo el MPS lee/escribe a Postgres local, no depende de ERP en tiempo real

2. **Sync incremental con cursores:** Evita full syncs costosos. Tabla `sync_cursors` trackea última sync por ERP/entity

3. **Circuit breaker para ERPs:** Sistema sigue operando si ERP cae. Estados: CLOSED → OPEN → HALF_OPEN

4. **Conflict resolution automático:**
   - ERP manda: fechas, cantidades, WIP
   - MPS manda: prioridades, asignaciones, locked items

5. **Heurística vs Optimización exacta:** Greedy nearest-neighbor para velocidad (<5 min con 1000+ orders) vs MIP/CP (horas)

6. **Incremental replanning:** Solo recalcula lo necesario. Respeta WIP in_progress y locked items

7. **Explainability first:** Cada decisión tiene `planning_notes` explicando "por qué"

8. **Soft constraints con penalties:** Permite planes "factibles con excepciones"

---

## 4. PRÓXIMOS PASOS RECOMENDADOS

### Inmediato (Esta Semana)
1. **Crear database migrations para modelos MPS:**
   ```bash
   cd backend
   flask db migrate -m "Add MPS core models (resources, shifts, plans)"
   flask db upgrade
   ```

2. **Implementar Resource y ShiftCalendar models:**
   - Agregar a `backend/app/models/__init__.py`
   - Datos seed iniciales (3 líneas, 3 turnos/día)

3. **Implementar MPSPlan y MPSPlanItem models:**
   - Básicos sin todas las relaciones aún
   - Suficiente para Fase 1

### Corto Plazo (2-3 Semanas) - Fase 1
4. **Implementar `backend/app/services/mps_service.py`:**
   - Función `run_planning()` básica
   - Priorización multi-criterio
   - Asignación a recursos (capacidad diaria gruesa)
   - Sin secuenciación ni setups aún

5. **Implementar `backend/app/routes/mps.py`:**
   - `POST /api/mps/run` (parámetros mínimos)
   - `GET /api/mps/plan` (sin paginación aún)

6. **Crear frontend básico:**
   - `frontend/src/pages/MPSPlanView.jsx` (tabla simple)
   - `frontend/src/services/mpsApi.js`
   - Agregar ruta en `App.jsx`

7. **Pruebas de Fase 1:**
   - Crear 50 órdenes de prueba
   - Ejecutar planning
   - Verificar que órdenes se asignan por prioridad

### Mediano Plazo (1-2 Meses) - Fases 2-3
8. **Implementar shift-level capacity (Fase 2)**
9. **Implementar setup times y secuenciación (Fase 3)**
10. **Crear Gantt chart UI**

### Largo Plazo (3+ Meses) - Fases 4-7
11. **WIP integration y replanning incremental (Fase 4)**
12. **Material allocations y MRP-lite (Fase 5)**
13. **Enhanced ERP sync con circuit breaker (Fase 6)**
14. **Advanced UI con drag-and-drop (Fase 7)**

---

## 5. MÉTRICAS DE ÉXITO

### MVP (Fin Fase 1)
- [ ] Planning ejecuta en <30 segundos para 100 órdenes
- [ ] Órdenes se asignan a recursos respetando capacidad diaria
- [ ] Prioridades se calculan correctamente
- [ ] Plan se persiste en DB
- [ ] UI muestra plan básico

### Producción (Fin Fase 3)
- [ ] Planning ejecuta en <5 minutos para 1000+ órdenes
- [ ] Capacidad finita por turno respetada
- [ ] Setup ratio <15%
- [ ] Plan es explicable (planning_notes en todos los items)

### Madurez (Fin Fase 7)
- [ ] OTIF proyectado >90%
- [ ] WIP integration en tiempo real (<5 min latency)
- [ ] Replanning incremental funciona sin recalcular todo
- [ ] Circuit breakers protegen contra ERPs caídos
- [ ] UI Gantt interactivo en producción

---

## 6. RECURSOS Y REFERENCIAS

### Documentos de Diseño
- `DISEÑO_MPS.md` - Fundamentos y algoritmos
- `DISEÑO_MPS_PARTE2.md` - Integración ERP
- `DISEÑO_MPS_PARTE3.md` - APIs y UI
- `DISEÑO_MPS_PARTE4.md` - Implementación

### Código Implementado
- `backend/app/utils/auth_helpers.py` - JWT helpers
- `backend/app/services/csv_importer.py` - CSV validator
- `backend/celeryworker.py` - Celery worker
- `.env.example` - Template de secrets

### Configuración
- `docker-compose.yml` - Servicios (DB, Redis, Backend, Celery, Frontend)
- `config.yaml` - Configuración base (overrideable con .env)

---

## 7. CONTACTO Y SOPORTE

Para preguntas sobre la implementación:
- **Documentación técnica:** Ver diseño completo en los 4 archivos DISEÑO_MPS*.md
- **Criterios de aceptación:** Cada fase tiene criterios verificables
- **Testing:** Pruebas mínimas por fase incluidas en documentación

---

**Versión:** 1.0  
**Fecha:** 2024-02-03  
**Estado:** Diseño completo + P0 fixes implementados. Listo para Fase 1.
