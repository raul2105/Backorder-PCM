# Guía de Configuración: IP Allowlist para Endpoints de Escritura

## 📋 Resumen de Cambios

Se ha implementado una política consistente de **IP allowlist** para todos los endpoints de escritura (POST/PUT/PATCH/DELETE) excepto `/api/auth/login`.

### ✅ Características Implementadas

1. **Decorator reutilizable** `@require_allowed_ip` en `backend/app/middleware/ip_allowlist.py`
2. **Soporte para reverse proxy** con configuración `TRUST_PROXY`
3. **Validación de IP con CIDR** (192.168.1.0/24, 10.0.0.0/8, etc.)
4. **Tests completos** (15 casos de prueba) en `backend/tests/test_ip_allowlist.py`
5. **Documentación** en `config.yaml` con ejemplos

---

## 🛡️ Endpoints Protegidos

### Todos los endpoints de escritura excepto login:

**Backorder:**
- POST `/api/backorder` - Crear backorder
- PUT `/api/backorder/<id>/department-status` - Actualizar estado departamental
- PUT `/api/backorder/<id>/priority` - Actualizar prioridad
- PUT `/api/backorder/<id>/status` - Actualizar estado
- PUT `/api/backorder/<id>/items/<item_id>` - Actualizar item
- PUT `/api/backorder/batch/update-status` - Actualización masiva

**Admin:**
- POST `/api/admin/users` - Crear usuario
- PUT `/api/admin/users/<id>` - Actualizar usuario
- POST `/api/admin/tasks/sync-erps` - Disparar sync manual

**Auth:**
- POST `/api/auth/register` - Registrar usuario

**Settings:**
- PUT `/api/settings/network` - Actualizar configuración de red

**Import:**
- POST `/api/import/csv` - Importar CSV

**Production:**
- POST `/api/production/log` - Crear log de producción

**Logistics:**
- PUT `/api/logistics/shipment/<id>` - Actualizar envío

### ⚠️ Endpoints NO afectados:
- **Login:** `POST /api/auth/login` (siempre accesible)
- **Lectura:** Todos los `GET` (no están protegidos por IP)

---

## ⚙️ Configuración

### 1. Configuración en `config.yaml`

El archivo `config.yaml` incluye la sección `network`:

```yaml
# Configuración de Red y Control de Acceso por IP
network:
  # Trust Proxy: Habilitar cuando la app esté detrás de un reverse proxy (nginx, HAProxy, etc.)
  # Si es true, confía en el header X-Forwarded-For para obtener la IP real del cliente
  # Si es false, usa request.remote_addr directamente
  trust_proxy: false  # Cambiar a true si está detrás de reverse proxy
  
  # Allowlist de IPs: Lista de IPs o rangos CIDR permitidos para operaciones de escritura
  # Si la lista está vacía o no existe, TODOS los accesos están permitidos
  # Si tiene valores, SOLO las IPs listadas pueden hacer POST/PUT/PATCH/DELETE
  # Nota: Se gestiona en la DB (tabla SystemSetting, key='network.allowed_ips')
  # Ejemplos de configuración válida:
  #   - IP individual: ["192.168.1.100", "10.0.0.5"]
  #   - Rango CIDR: ["192.168.1.0/24", "10.0.0.0/8"]
  #   - Red completa: ["172.16.0.0/12"]
  #   - Permitir todo: [] (lista vacía)
  # 
  # IMPORTANTE: El endpoint /api/auth/login NO está afectado por esta allowlist
  # IMPORTANTE: Los endpoints de lectura (GET) NO están afectados por esta allowlist
```

### 2. Gestión de IPs en Base de Datos

La allowlist se almacena en la tabla `SystemSetting` con clave `network.allowed_ips`.

#### Opción A: Desde el endpoint `/api/settings/network`

**Configurar IPs permitidas:**
```bash
curl -X PUT http://localhost:5000/api/settings/network \
  -H "Authorization: Bearer <TOKEN_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_ips": ["192.168.1.100", "192.168.1.0/24", "10.0.0.5"]
  }'
```

**Consultar configuración actual:**
```bash
curl -X GET http://localhost:5000/api/settings/network \
  -H "Authorization: Bearer <TOKEN_ADMIN>"
```

**Respuesta:**
```json
{
  "allowed_ips": ["192.168.1.100", "192.168.1.0/24", "10.0.0.5"]
}
```

#### Opción B: Directamente en la base de datos

```sql
-- Ver configuración actual
SELECT * FROM system_settings WHERE key = 'network.allowed_ips';

-- Configurar allowlist (PostgreSQL con jsonb)
UPDATE system_settings 
SET value = '["192.168.1.100", "192.168.1.0/24", "10.0.0.5"]'::jsonb
WHERE key = 'network.allowed_ips';

-- Permitir todas las IPs (lista vacía)
UPDATE system_settings 
SET value = '[]'::jsonb
WHERE key = 'network.allowed_ips';

-- Eliminar configuración (permite todas las IPs)
DELETE FROM system_settings WHERE key = 'network.allowed_ips';
```

---

## 🌐 Configuración con Reverse Proxy

### Escenario 1: Sin Reverse Proxy (desarrollo local)

```yaml
# config.yaml
network:
  trust_proxy: false
```

- El sistema usa `request.remote_addr` directamente
- Ignora el header `X-Forwarded-For`

### Escenario 2: Con Reverse Proxy (nginx, HAProxy, AWS ALB)

```yaml
# config.yaml
network:
  trust_proxy: true  # ✅ IMPORTANTE: Habilitar
```

**Configuración de nginx:**
```nginx
server {
    listen 80;
    server_name backorder.empresa.com;

    location / {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Con `trust_proxy: true`, el sistema:
1. Lee el header `X-Forwarded-For`
2. Toma la **primera IP** (cliente original)
3. Valida contra la allowlist

**Ejemplo:**
```
X-Forwarded-For: 203.0.113.5, 192.168.1.1, 10.0.0.1
                  ↑ Esta IP se valida (cliente original)
```

⚠️ **ADVERTENCIA:** Solo habilitar `trust_proxy: true` si estás detrás de un reverse proxy confiable. De lo contrario, un atacante podría falsificar el header `X-Forwarded-For`.

---

## 🧪 Validación y Tests

### Ejecutar los tests

```bash
cd backend

# Tests específicos de IP allowlist
pytest tests/test_ip_allowlist.py -v

# Todos los tests
pytest -v
```

### Tests implementados (15 casos):

#### `test_ip_allowlist.py::TestIPAllowlist`
✅ `test_write_endpoint_without_allowlist_allows_all` - Sin config = permitir todo
✅ `test_write_endpoint_with_empty_allowlist_allows_all` - Lista vacía = permitir todo
✅ `test_write_endpoint_blocks_non_allowed_ip` - Bloquea IP no permitida (403)
✅ `test_write_endpoint_allows_exact_ip_match` - Permite coincidencia exacta
✅ `test_write_endpoint_allows_cidr_range` - Permite rango CIDR
✅ `test_read_endpoint_not_affected_by_allowlist` - GET no afectado
✅ `test_login_not_affected_by_allowlist` - Login no afectado
✅ `test_multiple_write_endpoints_protected` - Múltiples endpoints protegidos
✅ `test_x_forwarded_for_when_trust_proxy_disabled` - X-Forwarded-For ignorado
✅ `test_invalid_cidr_notation_handled` - CIDR inválido no causa error

#### `test_ip_allowlist.py::TestAllWriteEndpointsProtected`
✅ `test_all_post_endpoints_protected` - Todos los POST protegidos
✅ `test_all_put_endpoints_protected` - Todos los PUT protegidos

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Permitir solo red interna de oficina

```json
{
  "allowed_ips": ["192.168.1.0/24"]
}
```

### Ejemplo 2: Permitir múltiples oficinas

```json
{
  "allowed_ips": [
    "192.168.1.0/24",    // Oficina Central
    "192.168.2.0/24",    // Oficina Sucursal 1
    "10.0.0.0/8"         // Red VPN corporativa
  ]
}
```

### Ejemplo 3: Permitir IPs específicas

```json
{
  "allowed_ips": [
    "203.0.113.5",       // Servidor de integración
    "198.51.100.10",     // IP estática de admin
    "192.0.2.50"         // Workstation de producción
  ]
}
```

### Ejemplo 4: Permitir todo (desarrollo/staging)

```json
{
  "allowed_ips": []
}
```

O eliminar la configuración completamente.

---

## 🔍 Troubleshooting

### Problema: "Operación no permitida desde esta IP"

**Causa:** Tu IP no está en la allowlist.

**Solución:**
1. Verificar tu IP pública: `curl ifconfig.me`
2. Agregar tu IP a la allowlist:
   ```bash
   curl -X PUT http://localhost:5000/api/settings/network \
     -H "Authorization: Bearer <TOKEN>" \
     -d '{"allowed_ips": ["TU_IP_AQUI"]}'
   ```

### Problema: No puedo actualizar la configuración de red

**Causa:** Estás bloqueado por la allowlist actual.

**Solución:**
1. Acceder directamente a la base de datos:
   ```sql
   UPDATE system_settings 
   SET value = '[]'::jsonb 
   WHERE key = 'network.allowed_ips';
   ```
2. O eliminar la configuración:
   ```sql
   DELETE FROM system_settings WHERE key = 'network.allowed_ips';
   ```

### Problema: X-Forwarded-For no funciona

**Causa:** `trust_proxy` está en `false`.

**Solución:**
1. Editar `config.yaml`:
   ```yaml
   network:
     trust_proxy: true
   ```
2. Reiniciar la aplicación:
   ```bash
   docker-compose restart backend
   ```

### Problema: Login también está bloqueado

**Verificación:** El login NO debe estar protegido.

**Debug:**
```bash
# Verificar que login funciona
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Si login responde 403, revisar que el decorator `@require_allowed_ip` **NO** esté en la función `login()`.

---

## 🎯 Casos de Uso Recomendados

### 1. Producción - Alta Seguridad
```json
{
  "allowed_ips": [
    "192.168.10.0/24",   // Red interna
    "203.0.113.50"       // IP pública del admin
  ]
}
```
```yaml
network:
  trust_proxy: true  # Si está detrás de nginx/ALB
```

### 2. Staging - Seguridad Media
```json
{
  "allowed_ips": [
    "192.168.0.0/16",    // Toda la red corporativa
    "10.0.0.0/8"         // VPN corporativa
  ]
}
```

### 3. Desarrollo - Sin restricción
```json
{
  "allowed_ips": []
}
```
```yaml
network:
  trust_proxy: false
```

---

## 📝 Logging y Auditoría

Cada intento bloqueado genera:

1. **Log de aplicación:**
   ```
   WARNING: IP bloqueada: 203.0.113.99 intentó acceder a backorder.create_backorder
   ```

2. **Respuesta HTTP 403:**
   ```json
   {
     "error": "Operación no permitida desde esta IP",
     "ip": "203.0.113.99"
   }
   ```

3. **Audit Log (solo para accesos exitosos):**
   - Cuando la IP está permitida, se crea el audit log normalmente
   - El `user_id` del JWT se registra en la tabla `audit_log`

---

## 🔐 Mejores Prácticas

1. **Usar rangos CIDR** en lugar de IPs individuales cuando sea posible
2. **Habilitar `trust_proxy`** solo si estás detrás de un reverse proxy confiable
3. **Monitorear logs** para detectar intentos de acceso no autorizados
4. **Revisar periódicamente** la allowlist y remover IPs que ya no deban tener acceso
5. **Documentar** cada IP o rango agregado (quién, cuándo, por qué)
6. **Permitir todo en desarrollo** (`allowed_ips: []`) para no bloquear el flujo de trabajo

---

## 🆘 Soporte

Si tienes problemas con la configuración:

1. Revisar logs del backend: `docker-compose logs -f backend`
2. Verificar configuración: `GET /api/settings/network`
3. Validar tu IP: `curl ifconfig.me`
4. Ejecutar tests: `pytest tests/test_ip_allowlist.py -v`

Para restablecer configuración en caso de emergencia:
```sql
DELETE FROM system_settings WHERE key = 'network.allowed_ips';
```

---

## 📚 Referencias

- Archivo principal: [backend/app/middleware/ip_allowlist.py](backend/app/middleware/ip_allowlist.py)
- Tests: [backend/tests/test_ip_allowlist.py](backend/tests/test_ip_allowlist.py)
- Configuración: [config.yaml](config.yaml)
