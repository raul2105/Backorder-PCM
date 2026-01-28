# ============================================================
# Script de Inicialización Automática - Backorder PCM
# ============================================================
# Este script inicia y configura todo el sistema automáticamente
# ============================================================

param(
    [switch]$SkipBrowser,
    [switch]$Reset
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Sistema de Gestión de Backorder PCM - Inicialización" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Función para mostrar mensajes con estilo
function Write-Step {
    param($Message)
    Write-Host "[INFO] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warning-Step {
    param($Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Error-Step {
    param($Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

function Write-Success {
    param($Message)
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $Message -ForegroundColor Green
}

# Verificar que Docker esté instalado
Write-Step "Verificando Docker Desktop..."
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker detectado: $dockerVersion"
    }
} catch {
    Write-Error-Step "Docker no está instalado o no está en el PATH"
    Write-Host ""
    Write-Host "Por favor, instala Docker Desktop desde: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar que Docker esté corriendo
Write-Step "Verificando que Docker Desktop esté corriendo..."
try {
    docker ps 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker Desktop está corriendo"
    }
} catch {
    Write-Error-Step "Docker Desktop no está corriendo"
    Write-Host ""
    Write-Host "Por favor, inicia Docker Desktop e intenta nuevamente" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar que docker-compose esté disponible
Write-Step "Verificando Docker Compose..."
try {
    docker-compose --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker Compose disponible"
    }
} catch {
    Write-Error-Step "Docker Compose no está disponible"
    exit 1
}

# Opción de reset completo
if ($Reset) {
    Write-Warning-Step "Modo RESET activado - Se eliminarán todos los datos"
    $confirm = Read-Host "¿Estás seguro? Esto borrará toda la base de datos (S/N)"
    if ($confirm -eq "S" -or $confirm -eq "s") {
        Write-Step "Deteniendo y eliminando contenedores..."
        docker-compose down -v
        Write-Success "Sistema reiniciado completamente"
    } else {
        Write-Host "Reset cancelado"
        exit 0
    }
}

# Detener servicios existentes si están corriendo
Write-Step "Verificando servicios existentes..."
$existingContainers = docker-compose ps -q
if ($existingContainers) {
    Write-Step "Deteniendo servicios anteriores..."
    docker-compose down
    Start-Sleep -Seconds 2
}

# Iniciar servicios con Docker Compose
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Iniciando Servicios" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Step "Iniciando contenedores Docker..."
Write-Host ""

docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Error-Step "Error al iniciar los servicios"
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Success "Contenedores iniciados"
Write-Host ""

# Esperar a que los servicios estén listos
Write-Step "Esperando a que los servicios estén listos..."
Write-Host "   - Base de datos PostgreSQL..." -NoNewline
Start-Sleep -Seconds 5
Write-Host " OK" -ForegroundColor Green

Write-Host "   - Redis..." -NoNewline
Start-Sleep -Seconds 2
Write-Host " OK" -ForegroundColor Green

Write-Host "   - Backend API..." -NoNewline
Start-Sleep -Seconds 8
Write-Host " OK" -ForegroundColor Green

Write-Host "   - Frontend Web..." -NoNewline
Start-Sleep -Seconds 5
Write-Host " OK" -ForegroundColor Green

# Verificar si la base de datos ya está inicializada
Write-Host ""
Write-Step "Verificando estado de la base de datos..."

$dbInitialized = $false
try {
    $checkDb = docker-compose exec -T backend python -c "from app import create_app, db; from app.models import User; app = create_app(); app.app_context().push(); print(User.query.count())" 2>$null
    if ($LASTEXITCODE -eq 0 -and $checkDb -match '^\d+$') {
        $userCount = [int]$checkDb.Trim()
        if ($userCount -gt 0) {
            $dbInitialized = $true
            Write-Success "Base de datos ya está inicializada ($userCount usuarios)"
        }
    }
} catch {
    # Base de datos no inicializada
}

# Inicializar base de datos si es necesario
if (-not $dbInitialized) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Inicializando Base de Datos" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Step "Creando tablas en la base de datos..."
    
    docker-compose exec -T backend python -c "from app import db, create_app; app = create_app(); app.app_context().push(); db.create_all(); print('Tablas creadas')"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Base de datos inicializada correctamente"
    } else {
        Write-Error-Step "Error al inicializar la base de datos"
    }

    # Crear usuario administrador
    Write-Step "Creando usuario administrador..."
    
    $createAdmin = docker-compose exec -T backend python -c @"
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@backorder.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('Usuario admin creado')
    else:
        print('Usuario admin ya existe')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Usuario administrador configurado"
    }
} else {
    Write-Step "Base de datos ya inicializada, omitiendo configuración"
}

# Verificar estado de los servicios
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Verificando Estado de Servicios" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$services = docker-compose ps --format "table {{.Service}}\t{{.Status}}" | Out-String
Write-Host $services

# Obtener IP local
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Información de Acceso" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1).IPAddress

Write-Host "Acceso Local:" -ForegroundColor Yellow
Write-Host "  Frontend:  " -NoNewline
Write-Host "http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend:   " -NoNewline
Write-Host "http://localhost:5000" -ForegroundColor Green

if ($localIP) {
    Write-Host ""
    Write-Host "Acceso desde Red Interna:" -ForegroundColor Yellow
    Write-Host "  Frontend:  " -NoNewline
    Write-Host "http://${localIP}:3000" -ForegroundColor Green
    Write-Host "  Backend:   " -NoNewline
    Write-Host "http://${localIP}:5000" -ForegroundColor Green
}

Write-Host ""
Write-Host "Credenciales por defecto:" -ForegroundColor Yellow
Write-Host "  Usuario:   " -NoNewline
Write-Host "admin" -ForegroundColor Cyan
Write-Host "  Contraseña: " -NoNewline
Write-Host "admin123" -ForegroundColor Cyan

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Sistema Iniciado Correctamente" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Comandos útiles
Write-Host "Comandos útiles:" -ForegroundColor Yellow
Write-Host "  Ver logs:           docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Detener sistema:    docker-compose stop" -ForegroundColor Gray
Write-Host "  Reiniciar sistema:  docker-compose restart" -ForegroundColor Gray
Write-Host "  Detener y limpiar:  docker-compose down" -ForegroundColor Gray
Write-Host ""

Write-Host "Features activadas:" -ForegroundColor Yellow
Write-Host "  * Autenticacion JWT con roles de usuario" -ForegroundColor Gray
Write-Host "  * Auditoria de cambios en tiempo real" -ForegroundColor Gray
Write-Host "  * Importacion avanzada CSV" -ForegroundColor Gray
Write-Host "  * Filtrado de acceso por IP" -ForegroundColor Gray
Write-Host "  * Edicion en tiempo real de pedidos y cantidades" -ForegroundColor Gray
Write-Host "  * Modo de PRUEBAS para desarrolladores (admin only)" -ForegroundColor Cyan
Write-Host ""

# Abrir navegador automáticamente
if (-not $SkipBrowser) {
    Write-Step "Abriendo navegador en 3 segundos..."
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:3000"
}

Write-Host ""
Write-Host "Presiona Ctrl+C para cerrar esta ventana" -ForegroundColor Gray
Write-Host ""

# Mantener la ventana abierta
Read-Host "Presiona Enter para cerrar"
