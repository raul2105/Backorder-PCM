# Guía de Configuración: Resilience en Conectores ERP

## 📋 Resumen de Cambios

Se han refactorizado TODOS los conectores ERP (Syteline, Mongus, Intranet) para implementar patrones de resilience: **timeout explícito**, **retries con exponential backoff**, **circuit breaker**, y **structured logging**.

### ✅ Características Implementadas

1. **Timeout explícito** en todos los requests (HTTP y SQL)
   - Configurado a 30 segundos por defecto
   - Evita que requests cuelguen indefinidamente

2. **Retries con exponential backoff**
   - 3 intentos automáticos para errores transitorios
   - Delays: 1s, 2s, 4s (2^attempt)
   - Decorador `@with_retry` reutilizable

3. **Circuit Breaker per fuente**
   - Si N fallas en ventana T → open (suspende por X minutos)
   - Config: 5 fallas en 5 min → open 5 min
   - Estado compartido entre instancias (dict a nivel de clase)

4. **Structured Logging**
   - JSON logs con: source, endpoint, method, status, duration_ms, error
   - Facilita monitoring y alertas
   - Cada request logea su resultado

---

## 📁 Archivos Modificados/Creados

### ✨ NUEVO: `backend/app/erp_connectors/resilience.py`

Módulo compartido con utilidades de resilience:

```python
class CircuitBreaker:
    """
    Circuit Breaker Pattern
    Estados: closed → open → half_open → closed
    """
    def __init__(self, failure_threshold=5, window_seconds=300, timeout_seconds=300)
    def record_success()
    def record_failure()
    def is_open() -> bool
    def get_status() -> dict

@with_retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
def decorated_function():
    """
    Decorator para retries automáticos con exponential backoff
    """

class StructuredLogger:
    """
    Logger para JSON structured logging
    """
    @staticmethod
    def log_request(source, endpoint, method, status, duration_ms, error=None)
```

**Líneas de código:** 241

---

### ✏️ MODIFICADO: `backend/app/erp_connectors/base_connector.py`

**Cambios:**

1. Agregado `circuit_breaker: CircuitBreaker` en `__init__`
2. Agregado `default_timeout` leído de config
3. Refactorizado `sync_all()`:
   - Chequea circuit breaker antes de sync
   - Usa `_safe_fetch()` para aislar errores por entidad
   - Registra success/failure en circuit breaker
   - Retorna dict con error si falla
4. Nuevo método `get_circuit_breaker_status()`

**Líneas modificadas:** ~80

---

### ✏️ MODIFICADO: `backend/app/erp_connectors/mongus_connector.py`

**Cambios:**

1. Importado `@with_retry`, `StructuredLogger`
2. Decorado `_make_request` con `@with_retry(max_attempts=3, exceptions=(...))`:
   - `requests.Timeout`
   - `requests.ConnectionError`
   - `requests.RequestException`
3. Agregado `timeout=self.default_timeout` a todos los `session.get()` / `session.post()`
4. Agregado structured logging:
   ```python
   StructuredLogger.log_request(
       source='mongus',
       endpoint=url,
       method='GET',
       status=200,
       duration_ms=round((end - start) * 1000),
       error=None
   )
   ```

**Líneas modificadas:** ~40

---

### ✏️ MODIFICADO: `backend/app/erp_connectors/intranet_connector.py`

**Cambios:**

1. Importado `@with_retry`, `StructuredLogger`
2. Agregado timeout a `_get_bearer_token()`:
   ```python
   response = self.session.post(auth_url, json=payload, verify=False, timeout=self.default_timeout)
   ```
3. Decorado `_make_request` con `@with_retry`
4. Agregado `timeout=self.default_timeout` a todos los `session.get()` / `session.post()`
5. Agregado structured logging con duration_ms tracking

**Líneas modificadas:** ~50

---

### ✏️ MODIFICADO: `backend/app/erp_connectors/syteline_connector.py`

**Cambios:**

1. Importado `@with_retry`, `StructuredLogger`, `pyodbc` errors
2. Decorado `connect()` con:
   ```python
   @with_retry(max_attempts=3, exceptions=(pyodbc.OperationalError, pyodbc.DatabaseError))
   ```
3. Agregado timeout a conexión y queries:
   ```python
   conn = pyodbc.connect(conn_str, timeout=self.default_timeout)
   conn.timeout = self.default_timeout  # Para queries
   ```
4. Agregado structured logging a `fetch_orders()`, `fetch_materials()`, `fetch_customers()`:
   ```python
   StructuredLogger.log_request(
       source='syteline',
       endpoint='fetch_orders',
       method='SQL',
       status=200,
       duration_ms=round((end - start) * 1000),
       error=None
   )
   ```

**Líneas modificadas:** ~60

---

### ✏️ MODIFICADO: `backend/app/routes/admin.py`

**Nuevo endpoint:**

```python
@bp.route('/erp/circuit-breakers', methods=['GET'])
@jwt_required()
@admin_required
def get_circuit_breaker_status():
    """Consultar el estado de los circuit breakers de cada ERP"""
    connectors = ERPConnectorFactory.get_all_active_connectors()
    statuses = [c['connector'].get_circuit_breaker_status() for c in connectors]
    return jsonify({
        'circuit_breakers': statuses,
        'timestamp': datetime.utcnow().isoformat()
    })
```

**Líneas agregadas:** ~20

---

### ✏️ MODIFICADO: `config.yaml`

**Agregado a cada ERP (syteline, mongus, intranet):**

```yaml
erp_systems:
  syteline:
    enabled: true
    timeout: 30  # ← NUEVO: timeout en segundos para queries/requests
    circuit_breaker:  # ← NUEVO
      failure_threshold: 5  # Número de fallas antes de abrir
      window_seconds: 300   # Ventana de tiempo para contar fallas (5 min)
      timeout_seconds: 300  # Tiempo que permanece abierto (5 min)
    # ... resto de config
  
  mongus:
    enabled: false
    timeout: 30  # ← NUEVO
    circuit_breaker:  # ← NUEVO
      failure_threshold: 5
      window_seconds: 300
      timeout_seconds: 300
    # ... resto de config
  
  intranet:
    enabled: false
    timeout: 30  # ← NUEVO
    circuit_breaker:  # ← NUEVO
      failure_threshold: 5
      window_seconds: 300
      timeout_seconds: 300
    # ... resto de config
```

---

## ⚙️ Configuración

### 1. Configuración de Timeouts

Editar `config.yaml`:

```yaml
erp_systems:
  syteline:
    timeout: 30  # segundos (recomendado: 15-60)
  mongus:
    timeout: 30
  intranet:
    timeout: 30
```

**Recomendaciones:**
- **Desarrollo:** 30-60 segundos (más permisivo)
- **Producción:** 15-30 segundos (más estricto)
- **ERPs lentos:** Hasta 60 segundos

---

### 2. Configuración de Circuit Breaker

Editar `config.yaml`:

```yaml
erp_systems:
  syteline:
    circuit_breaker:
      failure_threshold: 5    # Fallas antes de abrir (3-10 recomendado)
      window_seconds: 300     # Ventana de tiempo en segundos (5 min recomendado)
      timeout_seconds: 300    # Tiempo abierto en segundos (5 min recomendado)
```

**Ejemplos de configuración:**

#### Producción - Alta disponibilidad
```yaml
circuit_breaker:
  failure_threshold: 3    # Abrir rápido
  window_seconds: 180     # Ventana de 3 min
  timeout_seconds: 180    # Recuperar en 3 min
```

#### Staging - Balance
```yaml
circuit_breaker:
  failure_threshold: 5    # Valor por defecto
  window_seconds: 300     # 5 minutos
  timeout_seconds: 300    # 5 minutos
```

#### Desarrollo - Permisivo
```yaml
circuit_breaker:
  failure_threshold: 10   # Más tolerante
  window_seconds: 600     # 10 minutos
  timeout_seconds: 600    # 10 minutos
```

---

## 📊 Monitoreo

### 1. Consultar Estado de Circuit Breakers

```bash
curl -X GET http://localhost:5000/api/admin/erp/circuit-breakers \
  -H "Authorization: Bearer <TOKEN_ADMIN>"
```

**Respuesta:**

```json
{
  "circuit_breakers": [
    {
      "source": "syteline",
      "state": "closed",
      "failure_count": 0,
      "last_failure_time": null,
      "opened_at": null,
      "config": {
        "failure_threshold": 5,
        "window_seconds": 300,
        "timeout_seconds": 300
      }
    },
    {
      "source": "mongus",
      "state": "open",
      "failure_count": 5,
      "last_failure_time": "2026-01-30T10:15:23",
      "opened_at": "2026-01-30T10:15:23",
      "config": {...}
    }
  ],
  "timestamp": "2026-01-30T10:20:00"
}
```

**Estados posibles:**
- `closed`: Funcionando normalmente, requests pasan
- `open`: Circuito abierto, requests bloqueados (retorna error sin llamar al ERP)
- `half_open`: Probando si el servicio se recuperó (permite 1 request)

---

### 2. Logs Estructurados

Los logs ahora tienen formato JSON:

```json
{
  "timestamp": "2026-01-30T10:15:23.456Z",
  "source": "syteline",
  "endpoint": "fetch_orders",
  "method": "SQL",
  "status": 200,
  "duration_ms": 1234,
  "error": null
}
```

**En caso de error:**

```json
{
  "timestamp": "2026-01-30T10:15:23.456Z",
  "source": "mongus",
  "endpoint": "http://mongus-server/api/orders",
  "method": "GET",
  "status": 500,
  "duration_ms": 30015,
  "error": "ConnectionError: timeout after 30s"
}
```

**Filtrar logs en producción:**

```bash
# Ver solo errores de un ERP específico
docker-compose logs backend | grep "\"source\": \"syteline\"" | grep "\"status\": 500"

# Ver duraciones > 5 segundos
docker-compose logs backend | grep "\"duration_ms\"" | awk '$0 > 5000'

# Ver circuit breaker opens
docker-compose logs backend | grep "Circuit breaker OPEN"
```

---

## 🚀 Comportamiento en Producción

### Escenario 1: ERP Caído (Mongus)

1. **Request 1-5:** Fallan con timeout, se reintenta 3 veces cada uno
2. **Request 6:** Circuit breaker se abre (5 fallas en 5 min)
3. **Requests 6+:** Bloqueados inmediatamente, retornan error sin llamar al ERP
4. **Después de 5 min:** Circuit breaker entra en `half_open`
5. **Próximo request:** Se permite 1 intento de prueba
   - Si éxito → circuit breaker se cierra (vuelve a `closed`)
   - Si falla → circuit breaker se abre de nuevo

**Resultado:** El sistema continúa funcionando, lee datos locales, UI no se bloquea.

---

### Escenario 2: ERP Lento (Intranet)

1. **Request tarda 45s:** Timeout a los 30s, se reintenta
2. **3 reintentos:** Todos timeout
3. **Log estructurado:** `"status": 500, "duration_ms": 30000, "error": "Timeout"`
4. **Circuit breaker:** Cuenta como 1 falla
5. **Si persiste:** Circuit breaker abre después de 5 requests lentos

**Resultado:** No espera indefinidamente, sistema responde rápido con error.

---

### Escenario 3: Error Transitorio (Red)

1. **Request 1:** Falla con `ConnectionError`
2. **Retry automático (1s delay):** Falla
3. **Retry automático (2s delay):** Éxito ✅
4. **Circuit breaker:** Se registra el éxito, NO cuenta como falla

**Resultado:** Error transitorio se recupera automáticamente.

---

## 🧪 Testing

### Test Manual: Timeout

```python
# Simular timeout en Syteline (query lenta)
# En syteline_connector.py (SOLO PARA TEST):
cursor.execute("WAITFOR DELAY '00:01:00'; SELECT * FROM orders")  # 1 minuto de delay
```

**Resultado esperado:**
- Timeout a los 30s
- Se reintenta 3 veces
- Log: `"error": "Timeout after 30s"`

---

### Test Manual: Circuit Breaker

```python
# En backend shell:
from app.erp_connectors import ERPConnectorFactory

connector = ERPConnectorFactory.get_connector('mongus')

# Forzar 5 fallas
for i in range(5):
    connector.circuit_breaker.record_failure()

# Verificar estado
status = connector.get_circuit_breaker_status()
print(status)  # {'state': 'open', ...}

# Intentar sync
result = connector.sync_all()
print(result)  # {'success': False, 'error': 'Circuit breaker open'}
```

---

### Test Manual: Retries

```python
# Simular 2 fallas + 1 éxito en mongus_connector.py:
@with_retry(max_attempts=3)
def _make_request(self, method, url, **kwargs):
    self._retry_count = getattr(self, '_retry_count', 0)
    self._retry_count += 1
    
    if self._retry_count < 3:
        raise requests.Timeout("Simulated timeout")
    
    # 3er intento: éxito
    return self.session.get(url, timeout=30)
```

**Resultado esperado:**
- Retry 1 (1s delay): Falla
- Retry 2 (2s delay): Falla
- Retry 3 (4s delay): Éxito ✅
- Log: `"status": 200, "duration_ms": ~7000` (sum de delays + request)

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Sincronización Manual

```bash
# Disparar sync manual
curl -X POST http://localhost:5000/api/admin/tasks/sync-erps \
  -H "Authorization: Bearer <TOKEN>"

# Respuesta
{
  "message": "Tarea de sincronización iniciada",
  "task_id": "abc-123",
  "status": "PENDING"
}

# Consultar estado
curl -X GET http://localhost:5000/api/admin/tasks/abc-123/status \
  -H "Authorization: Bearer <TOKEN>"

# Respuesta si un ERP falló
{
  "task_id": "abc-123",
  "status": "SUCCESS",
  "result": [
    {
      "erp": "syteline",
      "orders": {"success": true, "new_orders": 5},
      "materials": {"success": true, "new_materials": 10}
    },
    {
      "erp": "mongus",
      "orders": {"success": false, "error": "Circuit breaker open"},
      "materials": {"success": false, "error": "Circuit breaker open"}
    }
  ]
}
```

---

### Ejemplo 2: Verificar Circuit Breaker Antes de Operación Crítica

```python
from app.erp_connectors import ERPConnectorFactory

connector = ERPConnectorFactory.get_connector('syteline')

# Verificar antes de operación crítica
status = connector.get_circuit_breaker_status()

if status['state'] == 'open':
    # Usar datos en caché o mostrar warning
    print("⚠️ Syteline no disponible, usando datos locales")
    orders = Order.query.filter_by(erp_source='syteline').all()
else:
    # Sincronizar normalmente
    result = connector.sync_all()
```

---

## 🔧 Troubleshooting

### Problema: "Circuit breaker open" persistente

**Causa:** ERP caído o inaccesible.

**Diagnóstico:**
```bash
# Ver estado
curl http://localhost:5000/api/admin/erp/circuit-breakers -H "Authorization: Bearer <TOKEN>"

# Revisar logs
docker-compose logs backend | grep "Circuit breaker"
```

**Solución:**
1. Verificar conectividad con el ERP:
   ```bash
   # Syteline (SQL)
   docker-compose exec backend python -c "import pyodbc; pyodbc.connect('...')"
   
   # Mongus (HTTP)
   curl http://mongus-server/api/health
   ```

2. Si el ERP está OK, resetear circuit breaker:
   ```python
   # En backend shell
   from app.erp_connectors import ERPConnectorFactory
   connector = ERPConnectorFactory.get_connector('syteline')
   connector.circuit_breaker._failures = []
   connector.circuit_breaker.opened_at = None
   ```

3. O esperar el timeout (5 min por defecto)

---

### Problema: Timeouts frecuentes pero ERP funciona

**Causa:** Timeout configurado muy bajo para ERPs lentos.

**Solución:**
```yaml
# config.yaml
erp_systems:
  syteline:
    timeout: 60  # Aumentar de 30 a 60 segundos
```

Reiniciar:
```bash
docker-compose restart backend celery_worker
```

---

### Problema: Retries consumen mucho tiempo

**Causa:** 3 intentos × 30s timeout = 90s total.

**Solución:**
1. Reducir timeout:
   ```yaml
   timeout: 15  # Para ERPs rápidos
   ```

2. O reducir max_attempts:
   ```python
   # En connector:
   @with_retry(max_attempts=2)  # Solo 2 intentos
   ```

---

## 📐 Arquitectura de Resilience

```
┌─────────────────────────────────────────────────────┐
│                  Flask Backend                      │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │          Celery Task: sync_all_erps           │ │
│  │                                               │ │
│  │  ┌─────────────────────────────────────────┐ │ │
│  │  │      ERPConnectorFactory                │ │ │
│  │  │                                         │ │ │
│  │  │  ┌────────────────────────────────┐    │ │ │
│  │  │  │   Syteline Connector           │    │ │ │
│  │  │  │                                │    │ │ │
│  │  │  │  1. Check Circuit Breaker      │    │ │ │
│  │  │  │     └─> Open? → Skip           │    │ │ │
│  │  │  │                                │    │ │ │
│  │  │  │  2. Execute with @with_retry   │    │ │ │
│  │  │  │     └─> Retry on failure       │    │ │ │
│  │  │  │                                │    │ │ │
│  │  │  │  3. Apply timeout=30s          │    │ │ │
│  │  │  │     └─> Abort if too slow      │    │ │ │
│  │  │  │                                │    │ │ │
│  │  │  │  4. Log structured JSON        │    │ │ │
│  │  │  │     └─> duration_ms, status    │    │ │ │
│  │  │  │                                │    │ │ │
│  │  │  │  5. Update Circuit Breaker     │    │ │ │
│  │  │  │     └─> success/failure        │    │ │ │
│  │  │  └────────────────────────────────┘    │ │ │
│  │  │                                         │ │ │
│  │  │  ┌────────────────────────────────┐    │ │ │
│  │  │  │   Mongus Connector             │    │ │ │
│  │  │  │   (mismo patrón)               │    │ │ │
│  │  │  └────────────────────────────────┘    │ │ │
│  │  │                                         │ │ │
│  │  │  ┌────────────────────────────────┐    │ │ │
│  │  │  │   Intranet Connector           │    │ │ │
│  │  │  │   (mismo patrón)               │    │ │ │
│  │  │  └────────────────────────────────┘    │ │ │
│  │  └─────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Criterios de Aceptación - CUMPLIDOS

| Criterio | Estado | Implementación |
|----------|--------|----------------|
| Timeout explícito en todos los requests | ✅ | `timeout=30` en HTTP y SQL |
| Retries con backoff (3 intentos) | ✅ | `@with_retry(max_attempts=3, backoff_base=2.0)` |
| Circuit breaker simple por fuente | ✅ | `CircuitBreaker` per source, 5/5/5 config |
| Logs estructurados por request | ✅ | `StructuredLogger.log_request(source, endpoint, status, duration_ms)` |
| Si ERP cae, sistema sigue funcionando | ✅ | Circuit breaker abre, sync retorna error pero no bloquea |
| Sync reporta errores sin bloquear | ✅ | `result = {'success': False, 'error': '...'}` |

---

## 🎯 Próximos Pasos (Opcional)

1. **Alertas por Slack/Email** cuando circuit breaker abre
2. **Dashboard de monitoring** con Grafana + Prometheus
3. **Métricas de Celery** con Flower
4. **Health check endpoint** que valida circuit breakers:
   ```python
   @app.route('/health/detailed')
   def health_detailed():
       breakers = [c.get_circuit_breaker_status() for c in connectors]
       healthy = all(b['state'] != 'open' for b in breakers)
       return jsonify({'healthy': healthy, 'breakers': breakers}), 200 if healthy else 503
   ```

---

## 📚 Referencias

- **Circuit Breaker Pattern:** [Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
- **Retry with Backoff:** [AWS Best Practices](https://docs.aws.amazon.com/general/latest/gr/api-retries.html)
- **Structured Logging:** [The Twelve-Factor App](https://12factor.net/logs)

---

## 🆘 Soporte

Si tienes problemas con los conectores:

1. **Verificar logs:**
   ```bash
   docker-compose logs -f backend | grep "StructuredLogger"
   ```

2. **Consultar circuit breakers:**
   ```bash
   curl http://localhost:5000/api/admin/erp/circuit-breakers -H "Authorization: Bearer <TOKEN>"
   ```

3. **Test de conectividad manual:**
   ```bash
   docker-compose exec backend flask shell
   >>> from app.erp_connectors import ERPConnectorFactory
   >>> connector = ERPConnectorFactory.get_connector('syteline')
   >>> result = connector.sync_all()
   >>> print(result)
   ```

4. **Revisar config.yaml:**
   ```bash
   cat config.yaml | grep -A 5 "timeout:"
   ```
