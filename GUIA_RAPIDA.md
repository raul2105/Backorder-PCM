# Guía Rápida de Inicio - Backorder PCM

## ⚡ Inicio Rápido (1 minuto)

### 1. Requisitos Mínimos
- Windows 10/11
- Docker Desktop instalado y corriendo
- 4GB RAM disponible
- Acceso a red de la empresa

### 2. Instalación Express - Método Simple 🚀

**Doble clic en:** `INICIAR.bat`

¡Eso es todo! El script automáticamente:
- ✅ Verifica que Docker esté corriendo
- ✅ Inicia todos los servicios
- ✅ Inicializa la base de datos
- ✅ Crea el usuario administrador
- ✅ Abre el navegador en la aplicación

### 3. Método Alternativo (PowerShell)

```powershell
# En PowerShell, navega a la carpeta del proyecto
cd "c:\Users\raul_\OneDrive\Escritorio\VS CODE Projects\Backorder PCM\Backorder-PCM"

# Ejecutar script de inicialización
.\iniciar.ps1
```

### 4. Acceder al Sistema

El navegador se abrirá automáticamente en: **http://localhost:3000**

**Credenciales:**
- Usuario: `admin`
- Contraseña: `admin123`

## 🔧 Configuración Básica

### Configurar tu ERP

1. Abrir archivo `config.yaml` en la raíz del proyecto

2. Para **INFOR Syteline**, modificar:
```yaml
erp_systems:
  syteline:
    enabled: true  # Cambiar a true para activar
    connection:
      server: "NOMBRE-SERVIDOR-SYTELINE"
      database: "SyteLine"
      username: "tu_usuario"
      password: "tu_password"
```

3. Reiniciar el backend:
```powershell
docker-compose restart backend
```

### Acceso desde Otros Equipos en la Red

1. Obtener IP del servidor:
```powershell
ipconfig
# Buscar IPv4 Address (ejemplo: 192.168.1.100)
```

2. Abrir firewall:
```powershell
New-NetFirewallRule -DisplayName "Backorder PCM" -Direction Inbound -LocalPort 3000,5000 -Protocol TCP -Action Allow
```

3. En otros equipos, acceder a:
```
http://192.168.1.100:3000
```

## 📋 Verificación del Sistema

### Comprobar que todo funciona:

```powershell
# Ver estado de los servicios
docker-compose ps

# Deberías ver:
# - backorder_db (running)
# - backorder_redis (running)
# - backorder_backend (running)
# - backorder_frontend (running)
# - backorder_celery (running)
```

### Probar conexión a ERP:

```powershell
docker-compose exec backend python -c "from app.erp_connectors import ERPConnectorFactory; connector = ERPConnectorFactory.get_connector('syteline'); print('Conexión:', 'OK' if connector.test_connection() else 'FALLO')"
```

## 🔄 Tareas Comunes

### 📂 Scripts Disponibles

El sistema incluye scripts ejecutables para facilitar la gestión:

| Script | Descripción | Uso |
|--------|-------------|-----|
| `INICIAR.bat` | Inicia todo el sistema automáticamente | Doble clic |
| `DETENER.bat` | Detiene todos los servicios | Doble clic |
| `iniciar.ps1` | Script PowerShell de inicialización | `.\iniciar.ps1` |
| `detener.ps1` | Detiene los servicios | `.\detener.ps1` |
| `estado.ps1` | Muestra el estado del sistema | `.\estado.ps1` |
| `ver-logs.ps1` | Visualiza logs en tiempo real | `.\ver-logs.ps1` |
| `reset.ps1` | Reset completo (elimina datos) | `.\reset.ps1` |

### Comandos Rápidos

**Detener el sistema:**
```powershell
.\detener.ps1
# o doble clic en DETENER.bat
```

**Ver estado del sistema:**
```powershell
.\estado.ps1
```

**Ver logs en tiempo real:**
```powershell
.\ver-logs.ps1
# o para un servicio específico:
.\ver-logs.ps1 backend
```

**Reiniciar sistema:**
```powershell
.\detener.ps1
.\iniciar.ps1
```

**Forzar sincronización con ERP:**
```powershell
docker-compose exec backend python -c "from app.services.sync_service import sync_all_erps; print(sync_all_erps())"
```

## ⚠️ Resolución Rápida de Problemas

### El sistema no inicia:
```powershell
# Opción 1: Reiniciar con script
.\detener.ps1
.\iniciar.ps1

# Opción 2: Reinicio manual
docker-compose down
docker-compose up -d
```

### Frontend muestra error de conexión:
```powershell
# Ver estado del sistema
.\estado.ps1

# Ver logs del backend
.\ver-logs.ps1 backend
```

### No puedo conectar al ERP:
1. Verificar conectividad: `ping SERVIDOR-ERP`
2. Verificar credenciales en `config.yaml`
3. Ver logs: `.\ver-logs.ps1 backend`

### Error en base de datos:
```powershell
# CUIDADO: Esto borra todos los datos
.\reset.ps1

# Luego reiniciar
.\iniciar.ps1
```

### Docker Desktop no está corriendo:
1. Abrir Docker Desktop manualmente
2. Esperar a que inicie completamente
3. Ejecutar `.\iniciar.ps1`

## 📞 Siguientes Pasos

1. ✅ Cambiar contraseña del usuario admin
2. ✅ Configurar conexión a tu ERP
3. ✅ Probar sincronización de datos
4. ✅ Configurar acceso desde otros equipos
5. ✅ Capacitar usuarios en el sistema

Para más detalles, consultar [DOCUMENTACION.md](DOCUMENTACION.md)

---

💡 **Tip:** Guarda esta guía para futuras referencias de mantenimiento
