# Celery Production-Ready Configuration

## 📋 Resumen de Cambios

Se ha reconfigurado Celery para que sea production-ready con las siguientes mejoras:

### ✅ Cambios Implementados

1. **Nuevo archivo `backend/celery_app.py`**
   - Crea la Flask app correctamente usando `create_app()`
   - Configura Celery con broker/backend desde config
   - Define `ContextTask` para usar `app.app_context()` automáticamente
   - Autodiscover e importa tasks de forma explícita
   - Configura tareas periódicas (Beat schedule)

2. **Actualizado `docker-compose.yml`**
   - Worker usa: `celery -A celery_app.celery worker -l info`
   - Beat usa: `celery -A celery_app.celery beat -l info`
   - Agregado servicio `celery_beat` para tareas periódicas

3. **Tasks registradas correctamente**
   - `sync_all_erps` ahora tiene nombre completo: `app.services.sync_service.sync_all_erps`
   - Import corregido para usar `celery_app` en lugar de `app.celery`

4. **Endpoints y comandos CLI agregados**
   - `POST /api/admin/tasks/sync-erps` - Disparar tarea manualmente
   - `GET /api/admin/tasks/<task_id>/status` - Consultar estado de tarea
   - `flask test-celery` - Disparar tarea desde CLI
   - `flask test-celery-sync` - Ejecutar sync de forma síncrona (debug)

---

## 🚀 Cómo Probar

### 1. Verificar la configuración (Local)

**En PowerShell:**
```powershell
cd backend
python verify_celery.ps1
```

Esto verificará:
- ✅ Que `celery_app.py` existe
- ✅ Que los imports funcionan correctamente
- ✅ Que la task `sync_all_erps` está registrada

---

### 2. Iniciar los servicios con Docker

```bash
# Levantar todos los servicios
docker-compose up -d

# O solo los servicios de Celery
docker-compose up -d celery_worker celery_beat
```

---

### 3. Verificar que el worker lista las tasks

```bash
# Ver logs del worker
docker-compose logs -f celery_worker
```

**Output esperado:**
```
✓ Task importada: app.services.sync_service.sync_all_erps

[tasks]
  . app.services.sync_service.sync_all_erps
```

---

### 4. Disparar una tarea manualmente

#### Opción A: Desde Flask CLI (dentro del container)

```bash
docker-compose exec backend flask test-celery
```

**Output esperado:**
```
🚀 Disparando tarea de sincronización de ERPs...
✅ Tarea disparada exitosamente
   Task ID: abc123-def456-ghi789
   Estado inicial: PENDING
```

#### Opción B: Desde el endpoint HTTP

Primero, obtener un token JWT:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Luego, disparar la tarea:
```bash
curl -X POST http://localhost:5000/api/admin/tasks/sync-erps \
  -H "Authorization: Bearer <TU_TOKEN>" \
  -H "Content-Type: application/json"
```

**Response esperado:**
```json
{
  "message": "Tarea de sincronización iniciada",
  "task_id": "abc123-def456-ghi789",
  "status": "PENDING"
}
```

---

### 5. Consultar el estado de la tarea

```bash
curl -X GET http://localhost:5000/api/admin/tasks/<TASK_ID>/status \
  -H "Authorization: Bearer <TU_TOKEN>"
```

**Response con éxito:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": [
    {
      "erp": "syteline",
      "orders": {"success": true, "new_orders": 5, "updated_orders": 2},
      "materials": {"success": true, "new_materials": 10, "updated_materials": 3}
    }
  ]
}
```

---

### 6. Verificar que la tarea escribió en DB

```bash
# Conectarse a la base de datos
docker-compose exec db psql -U pcm_user -d backorder_pcm

# Consultar las órdenes sincronizadas
SELECT order_number, customer_name, erp_source, last_sync 
FROM orders 
WHERE erp_source != 'manual' 
ORDER BY last_sync DESC 
LIMIT 10;
```

---

## 🐛 Debug: Ejecutar sync de forma síncrona

Si quieres probar la sincronización sin usar Celery (útil para debug):

```bash
docker-compose exec backend flask test-celery-sync
```

Esto ejecutará la sincronización directamente y mostrará los resultados en consola.

---

## 📊 Monitorear tareas con Flower (Opcional)

Para tener un dashboard de Celery, agregar a `docker-compose.yml`:

```yaml
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: backorder_flower
    command: celery -A celery_app.celery flower --port=5555
    environment:
      - DATABASE_URL=postgresql://pcm_user:pcm_password_2026@db:5432/backorder_pcm
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "5555:5555"
    depends_on:
      - redis
      - celery_worker
    networks:
      - backorder_network
```

Luego: `pip install flower` y acceder a `http://localhost:5555`

---

## ✅ Criterios de Aceptación - CUMPLIDOS

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| Al levantar docker-compose, celery worker lista tasks | ✅ | Worker muestra `app.services.sync_service.sync_all_erps` |
| No falla por missing app_context | ✅ | `ContextTask` envuelve todas las tasks con `app.app_context()` |
| Una tarea de sync puede correr y escribir en DB | ✅ | `sync_all_erps` usa `db.session.add()` y `commit()` sin errores |
| Comando/endpoint para disparar manualmente | ✅ | `flask test-celery` y `POST /api/admin/tasks/sync-erps` |

---

## 📁 Estructura de Archivos

```
backend/
├── celery_app.py                    ← ✨ NUEVO (configuración production-ready)
├── verify_celery.ps1                ← ✨ NUEVO (script de verificación)
├── verify_celery.sh                 ← ✨ NUEVO (script de verificación)
├── run.py                           ← ✏️ MODIFICADO (comandos CLI agregados)
├── app/
│   ├── __init__.py                  ← Sin cambios (Celery ya no se configura aquí)
│   ├── routes/
│   │   └── admin.py                 ← ✏️ MODIFICADO (endpoints de tasks)
│   └── services/
│       └── sync_service.py          ← ✏️ MODIFICADO (import de celery_app)
└── tests/
    └── ...
```

---

## 🔧 Configuración de Celery

### Timeouts configurados:
- **task_time_limit**: 30 minutos (hard limit)
- **task_soft_time_limit**: 25 minutos (soft limit)

### Beat Schedule:
- **sync-all-erps-every-hour**: Ejecuta `sync_all_erps` cada hora

### Optimizaciones:
- `worker_prefetch_multiplier=1`: No precargar tareas
- `worker_max_tasks_per_child=1000`: Reiniciar worker cada 1000 tareas
- `task_track_started=True`: Rastrear cuando inicia una tarea

---

## 🎯 Próximos Pasos (Opcional)

1. **Agregar más tasks**: Crear tasks adicionales en `app/services/` y se autodescubrirán
2. **Monitoring**: Instalar Flower para dashboard visual
3. **Alertas**: Configurar webhooks para notificar cuando una task falla
4. **Retry logic**: Agregar `autoretry_for` en las tasks que puedan fallar temporalmente
