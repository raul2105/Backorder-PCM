# Sistema de Gestión de Backorder PCM

Sistema completo para la gestión eficiente de backorders en plantas industriales de fabricación de etiquetas. Optimiza el flujo de materiales, producción, logística y entrega con integración a sistemas ERP como INFOR Syteline, MONGUS e intranet corporativa.

## 🎯 Características Principales

- **Gestión de Backorders**: Visualización y priorización automática de órdenes pendientes
- **Integración con ERPs**: Conectores para INFOR Syteline, MONGUS e intranet interna
- **Control de Inventario**: Monitoreo de materiales con alertas de stock bajo
- **Seguimiento de Producción**: Registro y tracking de procesos productivos
- **Gestión Logística**: Control de envíos y entregas
- **Dashboard en Tiempo Real**: Métricas y KPIs actualizados automáticamente
- **Compatible con Red Interna**: Diseñado para funcionar en redes corporativas

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  Dashboard │ Backorders │ Materiales │ Producción │ Logística│
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Backend (Flask)  │
                    │   API REST + JWT   │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐        ┌──────▼──────┐      ┌──────▼──────┐
   │PostgreSQL│        │   Redis     │      │   Celery    │
   │Database  │        │   Cache     │      │   Worker    │
   └──────────┘        └─────────────┘      └──────┬──────┘
                                                    │
                    ┌───────────────────────────────┘
                    │
        ┌───────────┴───────────────────────────┐
        │                                       │
   ┌────▼────────┐  ┌──────────┐  ┌───────────▼──┐
   │INFOR Syteline│  │  MONGUS  │  │   Intranet   │
   │    (ODBC)    │  │  (API)   │  │     (API)    │
   └──────────────┘  └──────────┘  └──────────────┘
```

## 📋 Requisitos Previos

### Software Necesario
- Docker y Docker Compose (recomendado)
- O instalación manual:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 16+
  - Redis 7+

### Acceso a Sistemas
- Credenciales de acceso a INFOR Syteline (ODBC/SQL Server)
- API keys para MONGUS (si aplica)
- Credenciales de intranet corporativa

## 🚀 Instalación y Configuración

### Opción 1: Instalación con Docker (Recomendada) - Método Automático 🚀

#### Instalación en 1 Paso:

**Simplemente ejecuta:** `INICIAR.bat` (doble clic)

El script automáticamente:
- ✅ Verifica que Docker esté instalado y corriendo
- ✅ Inicia todos los servicios (PostgreSQL, Redis, Backend, Frontend, Celery)
- ✅ Espera a que los servicios estén listos
- ✅ Inicializa la base de datos (solo primera vez)
- ✅ Crea el usuario administrador (solo primera vez)
- ✅ Muestra información de acceso
- ✅ Abre el navegador automáticamente

#### Método Manual (Alternativo):

1. **Configurar archivo config.yaml** (opcional en primera ejecución)
```yaml
erp_systems:
  syteline:
    enabled: true
    connection:
      server: "TU-SERVIDOR-SYTELINE"
      database: "SyteLine"
      username: "tu_usuario"
      password: "tu_password"
```

2. **Ejecutar script de PowerShell**
```powershell
.\iniciar.ps1
```

3. **Acceder a la aplicación**
- Frontend: http://localhost:3000 (se abre automáticamente)
- Backend API: http://localhost:5000
- Usuario: **admin** / Contraseña: **admin123**

#### Scripts de Gestión Disponibles:

| Script | Función |
|--------|---------|
| `INICIAR.bat` | Inicia todo el sistema |
| `DETENER.bat` | Detiene el sistema |
| `iniciar.ps1` | Script PowerShell de inicio |
| `detener.ps1` | Detiene servicios |
| `estado.ps1` | Muestra estado del sistema |
| `ver-logs.ps1` | Visualiza logs |
| `reset.ps1` | Reset completo (borra datos) |

### Opción 2: Instalación Manual

#### Backend

1. **Crear entorno virtual**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
```

2. **Instalar dependencias**
```powershell
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
Crear archivo `.env` en la carpeta `backend`:
```env
DATABASE_URL=postgresql://pcm_user:pcm_password@localhost:5432/backorder_pcm
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
```

4. **Inicializar base de datos**
```powershell
python run.py init_db
python run.py create_admin
```

5. **Ejecutar servidor**
```powershell
python run.py
```

#### Frontend

1. **Instalar dependencias**
```powershell
cd frontend
npm install
```

2. **Configurar variables de entorno**
Crear archivo `.env.local`:
```env
VITE_API_URL=http://localhost:5000/api
```

3. **Ejecutar en desarrollo**
```powershell
npm run dev
```

## ⚙️ Configuración para Red Interna

### Configuración de Red

1. **Obtener IP del servidor**
```powershell
ipconfig
```

2. **Configurar firewall (Windows)**
```powershell
New-NetFirewallRule -DisplayName "Backorder PCM Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Backorder PCM Backend" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

3. **Acceder desde otros equipos**
```
http://IP-DEL-SERVIDOR:3000
```

### Configuración de Conectores ERP

#### INFOR Syteline

Editar en `config.yaml`:
```yaml
erp_systems:
  syteline:
    enabled: true
    type: "odbc"
    connection:
      driver: "{ODBC Driver 17 for SQL Server}"
      server: "SERVIDOR-SYTELINE\\INSTANCIA"
      database: "SyteLine"
      username: "usuario_erp"
      password: "password_erp"
      trusted_connection: false
    sync_interval: 300  # Sincronizar cada 5 minutos
    tables:
      - "orders"
      - "items"
      - "inventory"
      - "production"
```

**Notas importantes:**
- Las queries en `backend/app/erp_connectors/syteline_connector.py` son **adaptables**
- Debes modificar los nombres de tablas y campos según tu instalación de Syteline
- Verifica el esquema de tu base de datos antes de usar

#### MONGUS

```yaml
erp_systems:
  mongus:
    enabled: false  # Cambiar a true cuando configures
    type: "api"
    base_url: "http://servidor-mongus/api"
    api_key: "TU_API_KEY"
    sync_interval: 300
```

#### Intranet Interna

```yaml
erp_systems:
  intranet:
    enabled: false  # Cambiar a true cuando configures
    type: "api"
    base_url: "http://intranet-servidor/api"
    auth_type: "basic"  # o "bearer", "digest"
    username: "usuario_api"
    password: "password_api"
    sync_interval: 600
```

## 📊 Uso del Sistema

### Dashboard Principal
- Vista general de backorders activos
- Alertas de materiales con stock bajo
- Estadísticas de producción
- Órdenes completadas

### Gestión de Backorders
- Lista completa de órdenes pendientes
- Filtros por estado, prioridad, cliente
- Actualización de prioridades
- Cambio de estados

### Control de Inventario
- Vista de todos los materiales
- Alertas de stock bajo
- Información de proveedores
- Tiempos de entrega

### Producción
- Registro de logs de producción
- Seguimiento por orden
- Control de calidad (rechazos)
- Asignación de máquinas y operadores

### Logística
- Órdenes listas para envío
- Historial de envíos
- Seguimiento de entregas

## 🔧 Mantenimiento y Soporte

### Ver Logs del Sistema

```powershell
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo frontend
docker-compose logs -f frontend
```

Los logs también se guardan en `logs/backorder.log`

### Backup de Base de Datos

```powershell
# Crear backup
docker-compose exec db pg_dump -U pcm_user backorder_pcm > "backup_$(Get-Date -Format 'yyyyMMdd').sql"

# Restaurar backup
Get-Content backup_20260123.sql | docker-compose exec -T db psql -U pcm_user backorder_pcm
```

### Actualización del Sistema

```powershell
# Detener servicios
docker-compose down

# Reconstruir contenedores
docker-compose build

# Iniciar servicios
docker-compose up -d
```

### Sincronización Manual con ERPs

```powershell
docker-compose exec backend python -c "from app.services.sync_service import sync_all_erps; sync_all_erps()"
```

### Troubleshooting Común

**Error de conexión a Syteline:**
1. Verifica conectividad al servidor de Syteline
2. Confirma que el driver ODBC esté instalado en el contenedor/servidor
3. Revisa las credenciales en `config.yaml`
4. Prueba la conexión:
```powershell
docker-compose exec backend python -c "from app.erp_connectors import ERPConnectorFactory; connector = ERPConnectorFactory.get_connector('syteline'); print(connector.test_connection())"
```

**Frontend no carga:**
1. Verifica que el backend esté corriendo: `docker-compose ps`
2. Revisa la consola del navegador (F12)
3. Confirma que `VITE_API_URL` apunte al backend correcto

**Base de datos no conecta:**
1. Verifica que PostgreSQL esté corriendo
2. Confirma las credenciales en `docker-compose.yml`
3. Revisa logs: `docker-compose logs db`

## 🔒 Seguridad

### Cambiar Contraseñas por Defecto

**⚠️ IMPORTANTE en Producción:**

1. **Usuario admin del sistema**: Cambiar después del primer login
2. **Base de datos**: Modificar en `docker-compose.yml` líneas 11-13
3. **Secret key**: Modificar en `config.yaml` línea 8

### Configurar HTTPS (Producción)

Se recomienda usar nginx como proxy inverso:

```nginx
server {
    listen 443 ssl;
    server_name backorder.empresa.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3000;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
    }
}
```

## 📱 API REST Documentation

### Endpoints Principales

**Autenticación:**
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Usuario actual

**Backorders:**
- `GET /api/backorder` - Listar backorders
- `GET /api/backorder/<id>` - Detalle
- `PUT /api/backorder/<id>/priority` - Actualizar prioridad
- `PUT /api/backorder/<id>/status` - Actualizar estado
- `GET /api/backorder/stats` - Estadísticas

**Materiales:**
- `GET /api/materials` - Listar materiales
- `GET /api/materials/alerts` - Alertas de stock

**Producción:**
- `GET /api/production/logs` - Logs de producción
- `POST /api/production/log` - Crear log

**Logística:**
- `GET /api/logistics/pending-shipments` - Pendientes
- `GET /api/logistics/shipped` - Enviadas

**Dashboard:**
- `GET /api/dashboard/overview` - Vista general
- `GET /api/dashboard/recent-activity` - Actividad reciente

### Ejemplo de Uso

```javascript
// Login
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});
const { access_token } = await response.json();

// Obtener backorders
const backorders = await fetch('http://localhost:5000/api/backorder', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

## 📁 Estructura del Proyecto

```
Backorder-PCM/
├── backend/                    # Backend Flask
│   ├── app/
│   │   ├── models/            # Modelos de base de datos
│   │   ├── routes/            # Endpoints API
│   │   ├── services/          # Lógica de negocio
│   │   └── erp_connectors/    # Conectores a ERPs
│   ├── run.py                 # Punto de entrada
│   ├── requirements.txt       # Dependencias Python
│   └── Dockerfile
├── frontend/                   # Frontend React
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas
│   │   └── services/          # Servicios API
│   ├── package.json
│   └── Dockerfile
├── config.yaml                 # Configuración principal
├── docker-compose.yml          # Orquestación Docker
└── README.md                   # Esta documentación
```

## 🤝 Soporte

Para soporte técnico:
1. Revisa esta documentación
2. Consulta los logs del sistema
3. Contacta al administrador

## 📝 Notas Importantes

1. **Adaptación de Queries ERP**: Las queries en los conectores son plantillas que deben adaptarse a tu esquema específico
2. **Primera Configuración**: Revisar y modificar `config.yaml` antes del primer uso
3. **Seguridad**: Cambiar todas las contraseñas por defecto en entorno de producción
4. **Red Interna**: El sistema funciona completamente offline una vez configurado
5. **Sincronización**: La frecuencia de sincronización es configurable en `config.yaml`

---

**Versión:** 1.0.0  
**Fecha:** Enero 2026  
**Sistema:** Backorder PCM para Gestión de Planta Industrial
