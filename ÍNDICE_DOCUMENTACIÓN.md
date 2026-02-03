# 📚 Índice de Documentación MPS - Backorder PCM

Este documento sirve como índice maestro para navegar toda la documentación del sistema Master Production Schedule (MPS).

---

## 🎯 Documento Inicial Recomendado

**START HERE:** [`RESUMEN_EJECUTIVO_MPS.md`](./RESUMEN_EJECUTIVO_MPS.md)

Este documento proporciona:
- Vista general de todo el proyecto
- Resumen de entregables completados
- Estado de implementación P0 fixes
- Próximos pasos recomendados
- Métricas de éxito

---

## 📖 Documentación por Tema

### 1. Diseño de Negocio y Modelos de Datos

**Archivo:** [`DISEÑO_MPS.md`](./DISEÑO_MPS.md)

**Contenido:**
- ✅ Definición del MPS para planta de etiquetas
  - Horizonte de planificación (2-8 semanas)
  - Buckets (turno/día/semana)
  - Unidades de medida (OT, metros, rollos)
  - KPIs completos (OTIF, tardiness, throughput, etc.)

- ✅ Entidades del negocio
  - Demanda, MPS Plan, MRP-lite, Capacidad, WIP Feedback

- ✅ Modelo de datos completo (PostgreSQL + SQLAlchemy)
  - 15+ tablas nuevas con DDL completo
  - Modificaciones a 4 tablas existentes
  - 20+ índices para performance
  - Tablas: Resources, ShiftCalendars, Routings, SetupTimes, MPSPlans, MPSPlanItems, WIPStates, MaterialAllocations, PlanningParameters, Constraints

- ✅ Algoritmo de planificación MPS
  - Pseudo-código completo en Python
  - 8 pasos: Preparación → Filtrado → Priorización → Programación → Secuenciación → Validación → Optimización → KPIs
  - Funciones de priorización detalladas
  - Algoritmo de secuenciación (TSP-like heuristic)
  - Cálculo de setup times

**Cuándo leer:** Primero, después del resumen ejecutivo. Para entender el negocio y la base de datos.

---

### 2. Integración con ERPs y Sincronización

**Archivo:** [`DISEÑO_MPS_PARTE2.md`](./DISEÑO_MPS_PARTE2.md)

**Contenido:**
- ✅ Datos a extraer por sistema ERP
  - **Syteline (ODBC/SQL Server):**
    - Queries SQL completas para: orders, WIP, inventory, BOM, routings, capacity
  - **Mongus (REST API):**
    - Endpoints GET con response examples
  - **Intranet (API Custom):**
    - Endpoints necesarios

- ✅ Estrategia de sincronización
  - Sync incremental con cursores (tabla `sync_cursors`)
  - Implementación Python de `ERPSyncService`
  - Nightly reconciliation (Celery task)
  - Detección de discrepancias

- ✅ Resolución de conflictos
  - Reglas claras: ERP vs Local
  - Función `ConflictResolution.resolve_order_conflict()`

- ✅ Resilience patterns
  - Circuit breaker implementation
  - Estados: CLOSED → OPEN → HALF_OPEN
  - Retry con exponential backoff
  - Uso en conectores ERP

**Cuándo leer:** Cuando implementes integración con ERPs. Después de tener modelos de datos.

---

### 3. APIs REST y Diseño de UI

**Archivo:** [`DISEÑO_MPS_PARTE3.md`](./DISEÑO_MPS_PARTE3.md)

**Contenido:**
- ✅ 7 Endpoints REST con ejemplos completos
  1. `POST /api/mps/run` - Ejecutar planificación
     - Request JSON con parámetros
     - Response con plan_id, KPIs, violations, blocked_orders
  2. `GET /api/mps/plan` - Obtener plan
     - Query params (filtros, pagination)
     - Response con plan_items array completo
  3. `PUT /api/mps/override` - Lock/move manual
     - Actions: lock, unlock, move, delete
  4. `GET /api/wip` - Estado WIP real-time
  5. `GET /api/mps/kpis` - Dashboard KPIs
  6. `GET /api/mps/exceptions` - Alertas y excepciones
  7. Implementación Python Flask completa

- ✅ 6 Pantallas UI con mockups ASCII
  1. **Gantt Chart** por recurso/turno
  2. **Backlog Priorizado** con ready/not-ready
  3. **Panel de Excepciones** (shortages, overload, tardiness)
  4. **KPI Dashboard** con charts
  5. **WIP Monitor** real-time
  6. Cada uno con:
     - Layout ASCII visual
     - Características detalladas
     - Componentes React necesarios

- ✅ Estructura de archivos frontend
  - Pages, Components, Services, Hooks
  - Rutas exactas de 20+ archivos a crear

**Cuándo leer:** Cuando implementes APIs y UI. Después de tener MPSService funcionando.

---

### 4. Plan de Implementación y Backlog

**Archivo:** [`DISEÑO_MPS_PARTE4.md`](./DISEÑO_MPS_PARTE4.md)

**Contenido:**
- ✅ Metodología incremental en 7 fases
  - **Fase 1:** MPS bucket diario (2-3 semanas)
    - Entregables: Modelos básicos, algoritmo simple, API mínima, UI básica
    - Criterios de aceptación con checkboxes
    - Pruebas específicas
  - **Fase 2:** Finite capacity + secuenciación (2-3 semanas)
  - **Fase 3:** Setups + tooling + optimización (3-4 semanas)
  - **Fase 4:** WIP integration (2-3 semanas)
  - **Fase 5:** Material allocation (2 semanas)
  - **Fase 6:** Enhanced sync + circuit breaker (2 semanas)
  - **Fase 7:** Advanced UI (3 semanas)

- ✅ Backlog priorizado (P0/P1/P2)
  - **P0 - CRÍTICO:** 4 items con soluciones detalladas
    - JWT identity bug (IMPLEMENTADO ✅)
    - Secrets en config (IMPLEMENTADO ✅)
    - CSV security (IMPLEMENTADO ✅)
    - Celery config (IMPLEMENTADO ✅)
  
  - **P1 - ALTA:** 4 items
    - Implementar modelos MPS core
    - MPSService básico
    - API routes MPS
    - Frontend MPS básico
  
  - **P2 - MEDIA:** 8 items
    - WIP models, Sync extensions, Setup times, Material allocations, etc.

- ✅ Estructura de archivos final
  - 60+ archivos listados con rutas exactas
  - Qué crear vs qué modificar

- ✅ Configuración sugerida
  - Sección completa para `config.yaml` con parámetros MPS

- ✅ Pruebas recomendadas
  - Unitarias, integración, carga
  - Por fase

- ✅ Documentación de usuario
  - Guías a crear

- ✅ Resumen de decisiones clave
  - 8 decisiones arquitectónicas fundamentales

**Cuándo leer:** Antes de empezar a programar. Para planificar sprints y prioridades.

---

## 🔍 Documentos de Soporte

### Configuración y Secrets

**Archivo:** [`.env.example`](./.env.example)

**Contenido:**
- Template completo de variables de entorno
- SECRET_KEY, JWT_SECRET_KEY
- Database credentials
- ERP credentials (Syteline, Mongus, Intranet)
- SMTP settings

**Uso:**
```bash
cp .env.example .env
nano .env  # Editar con valores reales
```

**Cuándo usar:** Al configurar el entorno de desarrollo o producción.

---

### Código Implementado (P0 Fixes)

**Archivos:**
- `backend/app/utils/auth_helpers.py` - JWT identity helpers
- `backend/app/routes/importer.py` - CSV upload seguro
- `backend/app/services/csv_importer.py` - Validación y sanitización
- `backend/celeryworker.py` - Celery worker
- `docker-compose.yml` - Servicios Docker

**Cuándo revisar:** Para entender las correcciones P0 implementadas.

---

## 🗺️ Guía de Lectura por Rol

### Para **Arquitecto/Tech Lead:**
1. 📄 `RESUMEN_EJECUTIVO_MPS.md` (overview)
2. 📄 `DISEÑO_MPS.md` (sección 1: Definición del MPS)
3. 📄 `DISEÑO_MPS.md` (sección 3: Algoritmo)
4. 📄 `DISEÑO_MPS_PARTE4.md` (sección 13: Decisiones)
5. 📄 `DISEÑO_MPS_PARTE4.md` (sección 7: Metodología)

**Tiempo total:** ~2 horas

---

### Para **DBA/Backend Developer:**
1. 📄 `RESUMEN_EJECUTIVO_MPS.md` (overview)
2. 📄 `DISEÑO_MPS.md` (sección 2: Modelo de datos completo)
3. 📄 `DISEÑO_MPS_PARTE2.md` (sección 4: Integración ERPs - queries SQL)
4. 📄 `DISEÑO_MPS_PARTE4.md` (sección 9: Estructura de archivos)

**Tiempo total:** ~3 horas

---

### Para **Backend/API Developer:**
1. 📄 `RESUMEN_EJECUTIVO_MPS.md` (overview)
2. 📄 `DISEÑO_MPS.md` (sección 3: Algoritmo - pseudo-código)
3. 📄 `DISEÑO_MPS_PARTE3.md` (sección 5: APIs REST - todos los endpoints)
4. 📄 `DISEÑO_MPS_PARTE4.md` (Fase 1: Entregables y criterios)

**Tiempo total:** ~2.5 horas

---

### Para **Frontend Developer:**
1. 📄 `RESUMEN_EJECUTIVO_MPS.md` (overview)
2. 📄 `DISEÑO_MPS.md` (sección 1.2: KPIs - para entender qué mostrar)
3. 📄 `DISEÑO_MPS_PARTE3.md` (sección 5: APIs REST - payloads JSON)
4. 📄 `DISEÑO_MPS_PARTE3.md` (sección 6: UI - todas las pantallas)

**Tiempo total:** ~2 horas

---

### Para **DevOps/SysAdmin:**
1. 📄 `RESUMEN_EJECUTIVO_MPS.md` (sección 2: P0 fixes)
2. 📄 `.env.example` (variables de entorno)
3. 📄 `DISEÑO_MPS_PARTE2.md` (sección 4.4: Resilience patterns)
4. 📄 `docker-compose.yml` (servicios)
5. 📄 `backend/celeryworker.py` (worker Celery)

**Tiempo total:** ~1 hora

---

### Para **Product Owner/Manager:**
1. 📄 `RESUMEN_EJECUTIVO_MPS.md` (completo)
2. 📄 `DISEÑO_MPS.md` (sección 1: Definición del MPS para negocio)
3. 📄 `DISEÑO_MPS_PARTE3.md` (sección 6.1: Pantallas UI - mockups)
4. 📄 `DISEÑO_MPS_PARTE4.md` (sección 7: Metodología - fases y timeline)

**Tiempo total:** ~1.5 horas

---

## 📊 Estadísticas de la Documentación

- **Total de páginas:** ~150 páginas
- **Archivos de diseño:** 5 documentos (4 partes + ejecutivo + índice)
- **Tablas de base de datos diseñadas:** 15+ nuevas, 4 modificadas
- **Endpoints REST diseñados:** 7 con payloads completos
- **Pantallas UI diseñadas:** 6 con mockups
- **Archivos de código a crear/modificar:** 60+
- **Fases de implementación:** 7 fases (16-23 semanas total)
- **P0 fixes implementados:** 4/4 (100%)
- **Líneas de pseudo-código:** 500+
- **Queries SQL ejemplo:** 10+
- **Decisiones arquitectónicas documentadas:** 8 clave

---

## 🚀 Flujo Recomendado para Implementación

```
START
  ↓
1. Leer RESUMEN_EJECUTIVO_MPS.md (30 min)
  ↓
2. Leer DISEÑO_MPS.md completo (2-3 horas)
  ↓
3. Crear migraciones de base de datos (1 día)
  ↓
4. Implementar Fase 1 - seguir DISEÑO_MPS_PARTE4.md (2-3 semanas)
  ↓
5. Leer DISEÑO_MPS_PARTE3.md para APIs (1 hora)
  ↓
6. Implementar APIs básicas (1 semana)
  ↓
7. Implementar UI básica (1 semana)
  ↓
8. Pruebas de Fase 1 (3 días)
  ↓
9. Leer DISEÑO_MPS_PARTE2.md para integración (2 horas)
  ↓
10. Continuar con Fases 2-7 según plan
  ↓
END (MPS completo en producción)
```

---

## 🔗 Links Rápidos

| Documento | Descripción | Tiempo Lectura |
|-----------|-------------|----------------|
| [RESUMEN_EJECUTIVO_MPS.md](./RESUMEN_EJECUTIVO_MPS.md) | Overview completo | 30 min |
| [DISEÑO_MPS.md](./DISEÑO_MPS.md) | Negocio + Datos + Algoritmo | 3 horas |
| [DISEÑO_MPS_PARTE2.md](./DISEÑO_MPS_PARTE2.md) | Integración ERPs | 2 horas |
| [DISEÑO_MPS_PARTE3.md](./DISEÑO_MPS_PARTE3.md) | APIs + UI | 2 horas |
| [DISEÑO_MPS_PARTE4.md](./DISEÑO_MPS_PARTE4.md) | Implementación + Backlog | 2 horas |
| [.env.example](./.env.example) | Configuración secrets | 10 min |

---

## ❓ FAQ

**P: ¿Por dónde empiezo?**
**R:** Lee `RESUMEN_EJECUTIVO_MPS.md` primero (30 minutos). Te da el contexto completo.

**P: ¿Necesito leer todo antes de programar?**
**R:** No. Lee el resumen ejecutivo + `DISEÑO_MPS.md` completo + Fase 1 de `DISEÑO_MPS_PARTE4.md`. Total: ~4 horas. Suficiente para empezar.

**P: ¿Cuánto tiempo tomará implementar todo?**
**R:** 16-23 semanas (4-6 meses) para MPS completo. MVP (Fase 1): 2-3 semanas.

**P: ¿Qué está ya implementado?**
**R:** Los 4 P0 fixes críticos (JWT, secrets, CSV security, Celery). Ver sección 2 de `RESUMEN_EJECUTIVO_MPS.md`.

**P: ¿Puedo implementar solo algunas fases?**
**R:** Sí. Cada fase es incremental y tiene criterios de aceptación independientes. Fase 1 ya da valor (planificación básica).

**P: ¿Dónde está el código del algoritmo MPS?**
**R:** Está en pseudo-código Python en `DISEÑO_MPS.md` sección 3. Listo para convertir a código real en `backend/app/services/mps_service.py`.

**P: ¿Las APIs están implementadas?**
**R:** No, solo diseñadas con payloads JSON completos en `DISEÑO_MPS_PARTE3.md`. Listas para implementar.

**P: ¿El UI está implementado?**
**R:** No, solo diseñado con mockups ASCII y estructura de componentes. Listo para implementar.

---

## 📞 Soporte

Para dudas sobre:
- **Arquitectura:** Ver decisiones en `DISEÑO_MPS_PARTE4.md` sección 13
- **Algoritmos:** Ver pseudo-código en `DISEÑO_MPS.md` sección 3
- **APIs:** Ver payloads en `DISEÑO_MPS_PARTE3.md` sección 5
- **Base de datos:** Ver DDL en `DISEÑO_MPS.md` sección 2
- **Implementación:** Ver fases en `DISEÑO_MPS_PARTE4.md` sección 7

---

**Última actualización:** 2024-02-03  
**Versión documentación:** 1.0  
**Estado:** Diseño completo + P0 fixes implementados
