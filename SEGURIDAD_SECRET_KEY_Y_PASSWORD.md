# Guía: Cambios de Seguridad - Validación SECRET_KEY y Cambio Obligatorio de Contraseña

## 📋 Resumen de Cambios Implementados

Se ha endurecido la seguridad del sistema con las siguientes mejoras:

### ✅ 1. Validación de SECRET_KEY en Producción

**Backend:**
- El sistema ahora valida que `server.secret_key` no sea el valor por defecto `"CHANGE_THIS_IN_PRODUCTION"` cuando está en modo producción
- Si detecta una SECRET_KEY inválida en producción, el backend NO arranca y muestra un error claro
- En modo desarrollo (`FLASK_ENV=development` o `server.debug=true`), permite el valor por defecto para facilitar el desarrollo

**Archivo modificado:** [backend/app/__init__.py](backend/app/__init__.py)

```python
secret_key = (config.get('server', {}).get('secret_key') or '').strip()
is_debug = bool(config.get('server', {}).get('debug', False))
env_name = os.getenv('FLASK_ENV', 'production').lower()
is_production = env_name == 'production' and not is_debug
if is_production and (not secret_key or secret_key == 'CHANGE_THIS_IN_PRODUCTION'):
    raise RuntimeError(
        'Configuración insegura: SECRET_KEY inválida. '
        'Configura server.secret_key en config.yaml antes de iniciar en producción.'
    )
```

---

### ✅ 2. Campo `must_change_password` en Usuario

**Backend:**
- Nuevo campo booleano `must_change_password` en el modelo `User`
- Por defecto es `False`, pero el usuario admin creado por `flask create_admin` se marca con `True`

**Archivo modificado:** [backend/app/models/__init__.py](backend/app/models/__init__.py)

```python
class User(db.Model):
    # ... campos existentes
    must_change_password = db.Column(db.Boolean, default=False)
```

**Migración aplicada:** `7f3b6c7e0a11_add_must_change_password_to_users.py`

---

### ✅ 3. Middleware para Bloquear Admin sin Cambio de Contraseña

**Backend:**
- Middleware `before_request` que intercepta TODAS las peticiones
- Si el usuario es admin y `must_change_password=True`, bloquea la petición con 403
- Excepciones: `/api/auth/login`, `/api/auth/change-password`, `/api/auth/me`, `/health`

**Archivo modificado:** [backend/app/__init__.py](backend/app/__init__.py)

```python
@app.before_request
def enforce_admin_password_change():
    # ... validación JWT
    user = User.query.get(int(identity))
    if user and user.role == 'admin' and user.must_change_password:
        return jsonify({
            'error': 'Debe cambiar la contraseña antes de continuar',
            'must_change_password': True
        }), 403
```

---

### ✅ 4. Nuevo Endpoint `/api/auth/change-password`

**Backend:**
- Endpoint POST para cambiar contraseña
- Requiere autenticación JWT
- Valida contraseña actual antes de cambiar
- Al cambiar, marca `must_change_password=False`

**Archivo modificado:** [backend/app/routes/auth.py](backend/app/routes/auth.py)

```python
@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    # ... validación
    user.password_hash = generate_password_hash(new_password)
    user.must_change_password = False
    db.session.commit()
    return jsonify({'message': 'Contraseña actualizada correctamente'}), 200
```

---

### ✅ 5. Login Devuelve `must_change_password`

**Backend:**
- El endpoint `/api/auth/login` y `/api/auth/me` ahora incluyen el campo `must_change_password` en la respuesta

**Archivo modificado:** [backend/app/routes/auth.py](backend/app/routes/auth.py)

```python
return jsonify({
    'access_token': access_token,
    'user': {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'must_change_password': user.must_change_password  # ← NUEVO
    }
}), 200
```

---

### ✅ 6. Nueva Pantalla de Cambio de Contraseña (Frontend)

**Frontend:**
- Nuevo componente `ChangePassword.jsx`
- Formulario con: contraseña actual, nueva contraseña, confirmar contraseña
- Validación de coincidencia de contraseñas
- Redirección a dashboard tras cambio exitoso

**Archivo creado:** [frontend/src/pages/ChangePassword.jsx](frontend/src/pages/ChangePassword.jsx)

---

### ✅ 7. Servicio `changePassword` en API (Frontend)

**Frontend:**
- Nuevo método `changePassword` en `authService`
- Actualiza el usuario en `localStorage` tras cambio exitoso

**Archivo modificado:** [frontend/src/services/api.js](frontend/src/services/api.js)

```javascript
changePassword: async (currentPassword, newPassword) => {
  const response = await api.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword
  });
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const updatedUser = { ...user, must_change_password: false };
  localStorage.setItem('user', JSON.stringify(updatedUser));
  return response.data;
}
```

---

### ✅ 8. Redirección Automática a Cambio de Contraseña (Frontend)

**Frontend:**
- El componente `Login` detecta si el usuario debe cambiar contraseña
- Si `must_change_password=true`, redirige a `/change-password` en lugar de dashboard
- El componente `App` bloquea acceso a otras rutas si `must_change_password=true`

**Archivos modificados:**
- [frontend/src/pages/Login.jsx](frontend/src/pages/Login.jsx)
- [frontend/src/App.jsx](frontend/src/App.jsx)

```javascript
// Login.jsx
const result = await authService.login(username, password);
if (result?.user?.must_change_password) {
  setMustChangePassword(true);
  navigate('/change-password');
  return;
}

// App.jsx
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated) return <Navigate to="/login" />;
  if (mustChangePassword && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" />;
  }
  return children;
};
```

---

### ✅ 9. Usuario Admin Creado con Cambio Obligatorio

**Backend:**
- El comando `flask create_admin` ahora marca el usuario admin con `must_change_password=True`

**Archivo modificado:** [backend/run.py](backend/run.py)

```python
admin = User(
    username='admin',
    email='admin@backorder.com',
    password_hash=generate_password_hash('admin123'),
    role='admin',
    must_change_password=True  # ← NUEVO
)
```

---

## 🚀 Estado Actual

### ✅ Migración Aplicada

La migración `7f3b6c7e0a11_add_must_change_password_to_users` se aplicó correctamente:

```bash
INFO  [alembic.runtime.migration] Running upgrade bbf45e6fa095 -> 7f3b6c7e0a11, add must_change_password to users
```

### ✅ Servicios Docker Corriendo

```
NAME                      STATUS
backorder_backend         Up (0.0.0.0:5000->5000/tcp)
backorder_frontend        Up (0.0.0.0:3000->80/tcp)
backorder_db              Up (0.0.0.0:5432->5432/tcp)
backorder_redis           Up (0.0.0.0:6379->6379/tcp)
```

---

## 📝 Qué Hacer Ahora

### 1. Probar el Login

1. Abre el navegador en `http://localhost:3000/login`
2. Ingresa las credenciales:
   - Usuario: `admin`
   - Contraseña: `admin123`
3. El sistema debe redirigirte automáticamente a `/change-password`
4. Cambia la contraseña del admin
5. Tras cambiar, deberías poder acceder al dashboard

### 2. Verificar el Bloqueo

Si intentas acceder a cualquier endpoint (excepto los permitidos) sin cambiar la contraseña, obtendrás:

```json
{
  "error": "Debe cambiar la contraseña antes de continuar",
  "must_change_password": true
}
```

Status: `403 Forbidden`

### 3. Para Producción: Cambiar SECRET_KEY

**IMPORTANTE:** Antes de desplegar en producción, debes cambiar `server.secret_key` en `config.yaml`:

```yaml
# config.yaml
server:
  host: "0.0.0.0"
  port: 5000
  debug: false
  secret_key: "TU_SECRET_KEY_SEGURA_AQUI"  # ← Genera una clave segura
```

**Generar una SECRET_KEY segura:**

```python
import secrets
print(secrets.token_urlsafe(32))
```

O en bash:

```bash
openssl rand -base64 32
```

### 4. Actualizar docker-compose.yml para Producción

Cuando estés listo para producción, cambia `FLASK_ENV` de nuevo a `production`:

```yaml
# docker-compose.yml
backend:
  environment:
    - FLASK_ENV=production  # ← Cambiar de development a production
    - DATABASE_URL=postgresql://pcm_user:pcm_password_2026@db:5432/backorder_pcm
    - REDIS_URL=redis://redis:6379/0
```

**IMPORTANTE:** Solo hazlo DESPUÉS de actualizar `server.secret_key` en `config.yaml`, o el backend no arrancará.

---

## 🎯 Criterios de Aceptación - CUMPLIDOS

| Criterio | ✅ Estado | Implementación |
|----------|-----------|----------------|
| En prod, no inicia con secret_key default | ✅ | Validación en `create_app()` |
| Admin no puede operar sin cambiar password | ✅ | Middleware `before_request` bloquea con 403 |
| Endpoint `/api/auth/change-password` | ✅ | Implementado con validación de password actual |
| Frontend fuerza pantalla de cambio | ✅ | Redirección automática desde login y `ProtectedRoute` |
| Login devuelve `must_change_password` | ✅ | Campo agregado a respuesta de `/auth/login` y `/auth/me` |
| Usuario admin creado con flag=True | ✅ | `flask create_admin` marca `must_change_password=True` |
| Migración aplicada | ✅ | `7f3b6c7e0a11` aplicada en base de datos |

---

## 🔧 Troubleshooting

### Problema: Backend no arranca con "SECRET_KEY inválida"

**Causa:** Estás en modo producción con SECRET_KEY default.

**Solución:**
1. Cambiar `server.secret_key` en `config.yaml` a un valor seguro, O
2. Usar `FLASK_ENV=development` en `docker-compose.yml` (solo para desarrollo)

### Problema: Login funciona pero no redirige a cambio de contraseña

**Causa:** El usuario admin no tiene `must_change_password=True`.

**Solución:**
```bash
docker-compose exec backend python -c "
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    admin.must_change_password = True
    db.session.commit()
    print('✅ Admin marcado para cambio de contraseña')
"
```

### Problema: Cambio de contraseña falla con 401

**Causa:** Contraseña actual incorrecta.

**Solución:** Verifica que estás ingresando la contraseña actual correcta (`admin123` por defecto).

---

## 📚 Archivos Modificados/Creados

### Backend
- ✏️ `backend/app/__init__.py` - Validación SECRET_KEY + middleware bloqueo admin
- ✏️ `backend/app/models/__init__.py` - Nuevo campo `must_change_password`
- ✏️ `backend/app/routes/auth.py` - Endpoint `change-password` + campo en responses
- ✏️ `backend/run.py` - Admin creado con `must_change_password=True`
- ✨ `backend/migrations/versions/7f3b6c7e0a11_add_must_change_password_to_users.py` - Migración

### Frontend
- ✨ `frontend/src/pages/ChangePassword.jsx` - Nueva pantalla
- ✏️ `frontend/src/pages/Login.jsx` - Redirección si must_change_password
- ✏️ `frontend/src/App.jsx` - Ruta `/change-password` + bloqueo en `ProtectedRoute`
- ✏️ `frontend/src/services/api.js` - Método `changePassword`

### Docker
- ✏️ `docker-compose.yml` - `FLASK_ENV=development` (temporal para desarrollo)

---

## 🆘 Soporte

Si tienes problemas:

1. Verifica logs del backend:
   ```bash
   docker-compose logs -f backend
   ```

2. Verifica estado de la base de datos:
   ```bash
   docker-compose exec backend flask db current
   ```

3. Verifica usuario admin:
   ```bash
   docker-compose exec backend python -c "
   from app import create_app, db
   from app.models import User
   app = create_app()
   with app.app_context():
       admin = User.query.filter_by(username='admin').first()
       print(f'Admin: {admin.username}')
       print(f'Must change password: {admin.must_change_password}')
   "
   ```
